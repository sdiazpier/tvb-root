# -*- coding: utf-8 -*-
#
#
#  TheVirtualBrain-Scientific Package. This package holds all simulators, and
# analysers necessary to run brain-simulations. You can use it stand alone or
# in conjunction with TheVirtualBrain-Framework Package. See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2020, Baycrest Centre for Geriatric Care ("Baycrest") and others
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this
# program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#   CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
LEMS2python module implements a DSL code generation using a TVB-specific LEMS-based DSL.

.. moduleauthor:: Michiel. A. van der Vlag <m.van.der.vlag@fz-juelich.de>   
.. moduleauthor:: Marmaduke Woodman <marmaduke.woodman@univ-amu.fr>


        Usage: - create an modelfile.xml
               - import rateML
               - make instance: rateml(model_filename, language, your/XMLfolder, 'your/generatedModelsfolder')
        the current supported model framework languages are python and cuda.
        for new models models/__init.py__ is auto_updated if model is unfamiliar to tvb for py models
        model_class_name is the model_filename + 'T', so not to overwrite existing models. Be sure to add the t
        when simulating the model in TVB
        example model files:
            epileptor.xml
            generic2doscillatort.xml
            kuramoto.xml
            montbrio.xml
            reducedwongwang.xml

"""

import os, sys
import tvb.simulator.models
from mako.template import Template
import re
from tvb.basic.logger.builder import get_logger

# not ideal but avoids modifying  the vendored LEMS itself
# sys.path.append(os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir))))
# from lems.model.model import Model

from lems.model.model import Model

logger = get_logger(__name__)

class RateML:

    def __init__(self, model_filename, language='python', XMLfolder=None, GENfolder=None):
        self.model_filename = model_filename
        self.language = language
        self.XMLfolder = XMLfolder
        self.GENfolder = GENfolder

        # set file locations
        self.generated_model_location = self.set_generated_model_location()
        self.xml_location = self.set_XML_model_folder()

    def transform(self):

        try:
            # start templating
            model_str, validation = self.render_model()
            if len(validation)>0:
                return False, validation

            # write model to user submitted location
            self.write_model_file(self.generated_model_location, model_str)

            # if it is a TVB.py model, it should be familiarized.
            # TODO it make the whole Server reset the session.
            #if self.language.lower()=='python':
            #    self.familiarize_TVB(model_str)
            return True, ""
        except Exception as e:
            return False, str(e)

    @staticmethod
    def default_XML_folder():
        here = os.path.dirname(os.path.abspath(__file__))
        xmlpath = os.path.join(here, 'XMLmodels')
        return xmlpath

    def set_XML_model_folder(self):
        folder = self.XMLfolder or self.default_XML_folder()
        return os.path.join(folder, self.model_filename + '.xml') #.lower()

    @staticmethod
    def default_generation_folder():
        here = os.path.dirname(os.path.abspath(__file__))
        xmlpath = os.path.join(here, 'generatedModels')
        return xmlpath

    def set_generated_model_location(self):
        folder = self.GENfolder or self.default_generation_folder()
        lan = self.language.lower()
        if lan=='python':
            ext='.py'
        elif lan=='cuda':
            ext='.c'
        return os.path.join(folder, self.model_filename.lower() + ext)

    def model_template(self):
        here = os.path.dirname(os.path.abspath(__file__))
        tmp_filename = os.path.join(here, 'tmpl8_'+ self.language +'.py')
        template = Template(filename=tmp_filename)
        return template

    def XSD_validate_XML(self):

        ''' Use own validation instead of LEMS because of slight difference in definition file'''

        from lxml import etree
        from urllib.request import urlopen

        # Local XSD file location
        # schema_file = urlopen("file:///home/michiel/Documents/Repos/tvb-root/github/tvb-root/scientific_library/tvb/rateML/rML_v0.xsd")

        # Global XSD file location
        schema_file = urlopen(
            "https://raw.githubusercontent.com/DeLaVlag/tvb-root/xsdvalidation/scientific_library/tvb/rateML/rML_v0.xsd")
        xmlschema = etree.XMLSchema(etree.parse(schema_file))
        xmlschema.assertValid(etree.parse(self.xml_location))
        logger.info("True validation of {0} against {1}".format(self.xml_location, schema_file.geturl()))

    def powerswap(self, power):
        target = power.group(1)
        powersplit = target.split('^')
        powf = 'powf(' + powersplit[0] + ', ' + powersplit[1] + ')'
        target = '{' + target + '}'

        return target, powf

    def preprocess_model(self, model):

        ''' Do some preprocessing on the template to easify rendering '''
        try:
            # check if boundaries for state variables are present. contruct is not necessary in pymodels
            # python only
            svboundaries = False
            for i, sv in enumerate(model.component_types['derivatives'].dynamics.state_variables):
                if sv.exposure != 'None' and sv.exposure != '' and sv.exposure:
                    svboundaries = True
                    continue

            # check for component_types containing coupling in name and gather data.
            # multiple coupling functions could be defined in xml
            # cuda only
            couplinglist = list()
            for i, cplists in enumerate(model.component_types):
                if 'coupling' in cplists.name:
                    couplinglist.append(cplists)

            # only check whether noise is there, if so then activate it
            # cuda only
            noisepresent=False
            for ct in (model.component_types):
                if ct.name == 'noise':
                    noisepresent=True

            # see if nsig derived parameter is present for noise
            # cuda only
            modellist = model.component_types['derivatives']
            nsigpresent=False
            if noisepresent==True:
                for dprm in (modellist.derived_parameters):
                    if (dprm.name == 'nsig' or dprm.name == 'NSIG'):
                         nsigpresent=True

            # check for power symbol and parse to python (**) or c power (powf(x, y))
            # there are 5 locations where they can occur: Derivedvariable.value, ConditionalDerivedVariable.Case.condition
            # Derivedparameter.value, Time_Derivaties.value and Exposure.dimension
            # Todo make more generic, XML tag processing might be the key

            for cptype in model.component_types:
                powlst = model.component_types[cptype.name]
                # list of locations with mathmatical expressions with attribute 'value'
                power_parse_exprs_value = [powlst.derived_parameters, powlst.dynamics.derived_variables,
                                           powlst.dynamics.time_derivatives]
                for pwr_parse_object in power_parse_exprs_value:
                    for pwr_obj in pwr_parse_object:
                        if '^' in  pwr_obj.value:
                            if self.language=='python':
                                if hasattr(pwr_obj, 'name'):
                                    pwr_parse_object[pwr_obj.name].value = pwr_obj.value\
                                        .replace('{', '').replace('^', ' ** ').replace('}', '')
                                if hasattr(pwr_obj, 'variable'):
                                    pwr_parse_object[pwr_obj.variable].value = pwr_obj.value\
                                        .replace('{', '').replace('^', ' ** ').replace('}', '')
                            if self.language=='cuda':
                                for power in re.finditer('\{(.*?)\}',  pwr_obj.value):
                                    target, powf = self.powerswap(power)
                                    if hasattr(pwr_obj, 'name'):
                                        pwr_parse_object[pwr_obj.name].value = pwr_obj.value.replace(target, powf)
                                    if hasattr(pwr_obj, 'variable'):
                                        pwr_parse_object[pwr_obj.variable].value = pwr_obj.value.replace(target, powf)

                for pwr_obj in powlst.exposures:
                    if '^' in pwr_obj.dimension:
                        if self.language=='python':
                            powlst.exposures[pwr_obj.name].dimension = pwr_obj.dimension\
                                .replace('{', '').replace('^', ' ** ').replace('}', '')
                        if self.language=='cuda':
                            for power in re.finditer('\{(.*?)\}', pwr_obj.dimension):
                                target, powf = self.powerswap(power)
                                powlst.exposures[pwr_obj.name].dimension = pwr_obj.dimension.replace(target, powf)

                for cdv in powlst.dynamics.conditional_derived_variables:
                    for casenr, case in enumerate(cdv.cases):
                        if '^' in case.value:
                            if self.language == 'python':
                                powlst.dynamics.conditional_derived_variables[cdv.name].cases[casenr].value = case.value\
                                    .replace('{', '').replace('^', ' ** ').replace('}', '')
                            if self.language == 'cuda':
                                for power in re.finditer('\{(.*?)\}', case.value):
                                    target, powf = self.powerswap(power)
                                    powlst.dynamics.conditional_derived_variables[cdv.name].cases[casenr].value = case.value.replace(target, powf)

            return svboundaries, couplinglist, noisepresent, nsigpresent, ""
        except Exception as error:
            return None, None, None, None, str(error)

    def load_model(self):
        "Load model from filename"

        # instantiate LEMS lib
        model = Model()
        model.import_from_file(self.xml_location)

        self.XSD_validate_XML()

        # do some inventory. check if boundaries are set for any sv to print the boundaries section in template
        svboundaries, couplinglist, noisepresent, nsigpresent, error = self.preprocess_model(model)

        return model, svboundaries, couplinglist, noisepresent, nsigpresent, error

    def render_model(self):
        '''
        render_model start the mako templating.
        this function is similar for all languages. its .render arguments are overloaded.
        '''


        if self.language == 'python':
            model_class_name = self.model_filename.capitalize() + 'T'
        if self.language == 'cuda':
            model_class_name = self.model_filename

        validation = ""
        derivative_list = None
        model, svboundaries, couplinglist, noisepresent, nsigpresent, error = self.load_model()

        #Checking model
        if len(error)>0:
            validation +=error
        else:
            derivative_list = model.component_types['derivatives']


        #Checking minimum requirements
        if derivative_list != None:

            #Common Validation
            if len(list(derivative_list.constants)) == 0:
                validation += "Constant is missing.\n"
            if len(list(derivative_list.exposures)) == 0:
                validation += "Exposures is missing.\n"
            if derivative_list.dynamics == None:
                validation += "Dynamics is missing.\n"

            #Python Validation

            #Cuda Validation

        else:
            validation += "Derivatives component is missing.\n"

        if len(validation)>0:
            return None, validation

            # start templating
        model_str = self.model_template().render(
            modelname=model_class_name,                     # all
            const=derivative_list.constants,                # all
            dynamics=derivative_list.dynamics,              # all
            exposures=derivative_list.exposures,            # all
            params=derivative_list.parameters,              # cuda
            derparams=derivative_list.derived_parameters,   # cuda
            svboundaries=svboundaries,                      # python
            coupling=couplinglist,                          # cuda
            noisepresent=noisepresent,                      # cuda
            nsigpresent=nsigpresent,                        # cuda
            )

        return model_str, validation

    def familiarize_TVB(self, model_str):
        '''
        Write new model to TVB model location and into init.py such it is familiar to TVB if not already present
        This is for Python models only
        '''

        model_filename = self.model_filename
        # set tvb location
        TVB_model_location = os.path.join(os.path.dirname(tvb.simulator.models.__file__), model_filename.lower() + 'T.py')
        # next to user submitted location also write to default tvb location
        self.write_model_file(TVB_model_location, model_str)

        try:
            doprint = True
            modelenumnum = 0
            modulemodnum = 0
            with open(os.path.join(os.path.dirname(tvb.simulator.models.__file__), '__init__.py'), "r+") as f:
                lines = f.readlines()
                for num, line in enumerate(lines):
                    if (model_filename.upper() + 'T = ' + "\"" + model_filename.capitalize() + "T\"") in line:
                        doprint = False
                    elif ("class ModelsEnum(Enum):") in line:
                        modelenumnum = num
                    elif ("_module_models = {") in line:
                        modulemodnum = num
                if doprint:
                    lines.insert(modelenumnum + 1, "    " + model_filename.upper() + 'T = ' + "\"" +
                                 model_filename.capitalize() + "T\"\n")
                    lines.insert(modulemodnum + 2, "    " + "'" + model_filename.lower() + "T'" + ': '
                                 + "[ModelsEnum." + model_filename.upper() + "T],\n")
                    f.truncate(0)
                    f.seek(0)
                    f.writelines(lines)
                logger.info("model file generated {}".format(model_filename))
        except IOError as e:
            logger.error('ioerror: %s', e)

    def write_model_file(self, model_location, model_str):

        '''Write templated model to file'''

        with open(model_location, "w") as f:
            f.writelines(model_str)


if __name__ == "__main__":

    # language='python'
    language='cuda'

    # model_filename = 'montbrio'
    # model_filename = 'oscillator'
    # model_filename = 'kuramoto'
    model_filename = 'rwongwang'
    # model_filename = 'epileptor'

    RateML(model_filename, language, './XMLmodels/', './generatedModels/')

    # for simulation
    # from run.regular_run import regularRun
    # from matplotlib.pyplot import *
    #
    # simtime = 5000
    # g = 32
    # s = 32
    # dt = 1
    # period = 1.
    # # modelExec = 'KuramotoT'
    # modelExec = 'RwongwangT'
    # # modelExec = 'ReducedWongWang'
    # (time, data) = regularRun(simtime, g, s, dt, period).simulate_python(modelExec)
    #
    # figure()
    # plot(time, data[:, 0, :, 0], 'k', alpha=0.1)
    # show()

