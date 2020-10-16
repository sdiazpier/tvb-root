from mako.template import Template

import os,sys
from lxml import etree
from urllib.request import urlopen

# not ideal but avoids modifying  the vendored LEMS itself
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tvb.basic.logger.builder import get_logger
from tvb.dsl_cuda.lems.model.model import Model

logger = get_logger(__name__)


def default_lems_folder():
    here = os.path.dirname(os.path.abspath(__file__))
    xmlpath = os.path.join(here, 'XMLmodels')
    print(' - Input folder -> ', xmlpath, "(xxx_CUDA.xml)")
    return xmlpath

def lems_file(model_name, folder=None):
    folder = folder or default_lems_folder()
    return os.path.join(folder, model_name.lower() + '_CUDA.xml')

def default_template():
    here = os.path.dirname(os.path.abspath(__file__))
    tmp_filename = os.path.join(here, 'tmpl8_CUDA.py')
    template = Template(filename=tmp_filename)
    return template

def load_model(model_filename, folder=None):
    "Load model from filename"

    fp_xml = lems_file(model_filename, folder)

    model = Model()
    model.import_from_file(fp_xml)
    # modelextended = model.resolve()

    return model
def validate_LEMS_structure(filename, folder):
    try:
        xml_file_path = lems_file(filename, folder)
        schema_file = urlopen("https://raw.githubusercontent.com/LEMS/LEMS/development/Schemas/LEMS/LEMS_v0.7.3.xsd")
        xml_schema = etree.XMLSchema(etree.parse(schema_file))
        print("Validating", filename,"against",schema_file.geturl())
        xml_schema.assert_(etree.parse(xml_file_path))
        return ""

    except Exception as e:
        return "XSD" + str(e)

def checkValidation(model_name, model, folder):
    has_coupling = False
    for i, cplists in enumerate(model.component_types):
        if 'coupling' in cplists.name:
            has_coupling = True
            break
    has_noise = False
    for ct in (model.component_types):
        if ct.name == 'noise' and ct.description == 'on':
            has_noise = True
            break

    if model_name not in model.component_types:
        return "Model name is not in the component"
    elif len(list(model.component_types[model_name].constants)) == 0:
        return "Constant is missing!"
    elif model.component_types[model_name].dynamics == None:
        return "Model does not containt Dynamics"
    elif len(list(model.component_types[model_name].parameters)) == 0:
        return "There is not Parameters"
    elif len(list(model.component_types[model_name].derived_parameters)) == 0:
        return "There is not Derived Parameters"
    elif len(list(model.component_types[model_name].exposures)) == 0:
        return "There is not Exposures"
    elif not has_coupling:
        return "There is coupling in ComponentTypes"
    elif not has_noise:
        return "There is not noise in ComponentTypes"
    # elif(validator != None):
    #    return validate_LEMS_structure(model_name, validator, folder)
    else:
        return ""

def render_model(model_name, template=None, folder=None):
    model_str = ''
    try:
        model = load_model(model_name, folder)
        template = template or default_template()

        modellist = model.component_types[model_name]
        validation = checkValidation(model_name, model, folder)
        print("voy a validar")
        if len(validation) == 0:

            # coupling functionality
            couplinglist = list()
            for i, cplists in enumerate(model.component_types):
                if 'coupling' in cplists.name:
                    couplinglist.append(cplists)
            # collect total number of exposures combinations.
            expolist = list()
            for i, expo in enumerate(modellist.exposures):
                for chc in expo.choices:
                    expolist.append(chc)
            # only check whether noise is there, if so then activate it
            noisepresent=False
            for ct in (model.component_types):
                if ct.name == 'noise' and ct.description == 'on':
                    noisepresent=True
            # start templating
            model_str = template.render(
                                    modelname=model_name,
                                    const=modellist.constants,
                                    dynamics=modellist.dynamics,
                                    params=modellist.parameters,
                                    derparams=modellist.derived_parameters,
                                    coupling=couplinglist,
                                    noisepresent=noisepresent,
                                    expolist=expolist
                                    )
            return True, model_str
        else:
            model_str = validation

    except Exception as e:
        logger.error('Error %s', e)
        model_str = e

    return False, 'LEMS validation. ' + model_str

def cuda_templating(model_filename, folder=None):

    modelfile = os.path.join((os.path.dirname(os.path.abspath(__file__))), 'CUDAmodels', model_filename.lower() + '.c')
    print(' - Output folder -> ', os.path.join((os.path.dirname(os.path.abspath(__file__))), 'CUDAmodels'))
    #logger.info(" - Output folder -> %s", os.path.join(os.path.dirname(tvb.simulator.models.__file__)))

    # start templating
    validation, model_str = render_model(model_filename, template=default_template(), folder=folder)
    if not validation:
        return model_str

    # write template to file
    with open(modelfile, "w") as f:
        f.writelines(model_str)

    return ""

if __name__ == '__main__':

    # model_filename = 'Oscillator'
    # model_filename = 'Kuramoto'
    # model_filename = 'Rwongwang'
    model_filename = 'Epileptor'
    #cuda_templating(model_filename)
