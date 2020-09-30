import cherrypy, os
import tvb
from tvb.basic.logger.builder import get_logger
from tvb.core.services.exceptions import ServicesBaseException
from tvb.core.services.operation_service import OperationService
from tvb.interfaces.web.controllers import common
from tvb.interfaces.web.controllers.decorators import expose_page, using_template, settings, expose_fragment, \
    handle_error, check_user
from tvb.interfaces.web.controllers.flow_controller import FlowController
from tvb.interfaces.web.controllers.tools.tools_controller import ToolsController
import xml.etree.cElementTree as Xml

from tvb.dsl import LEMS2python as CodeGenerator

class DSLController(ToolsController):
    def __init__(self):
        ToolsController.__init__(self)
        self.operation_service = OperationService()
        self.logger = get_logger(__name__)

        self.dictAll = {}
        self.dictEsencial = {}
        self.dictStructuredIDs = {}
        self.dictModelInfo = {}

        #TODO Fix the real path
        #self.basepath = os.path.join(os.path.dirname(tvb.__file__),'dsl','NeuroML','XMLmodels')
        self.basepath = os.path.join(os.getenv("HOME"),'tvb_temporal_folder')

        self.xml_components={"ComponentType": "none",
         "Constant": "ComponentType",
         "Exposure": "ComponentType",
         "Dynamics": "none",
         "StateVariable": "Dynamics",
         "DerivedVariable": "Dynamics",
         "TimeDerivative": "Dynamics"}

        #ComponentType
        # - constant
        # - Dynamic
        #    - Variable

        self.dictComponentInfo = {'id': '', 'type': '', 'parent': ''}

        self.dictComponentType= {"ComponentType": {'name': '', 'description': '', 'value': ''},
                                "Constant": {'name': '', 'domain': '', 'default': '', 'description': ''},
                                "Exposure": {'name': '', 'choices': '', 'default': '', 'description': ''},
                                "Dynamics": {'name': ''},
                                "StateVariable": {'name': '', 'default': '', 'boundaries': ''},
                                "DerivedVariable": {'name': '', 'expression': ''},
                                "ConditionalDerivedVariable": {'name': '', 'cases': '', 'condition': ''},
                                "TimeDerivative": {'name': '', 'expression': ''}}

        #TODO: get the session id
        self.userID = 20

        self.dictAll[self.userID] = {}
        self.dictEsencial[self.userID] = {}
        self.dictStructuredIDs[self.userID] = {}
        self.dictModelInfo[self.userID] = {}

    @cherrypy.expose
    @handle_error(redirect=False)
    @check_user
    def convertdata(self, **data):
        try:
            for key, value in data.items():
                if(len(key) > 0):
                    self.dictModelInfo[self.userID][key] = value
            self.generateXML()

        except ServicesBaseException as excep:
            self.logger.error("Could not convert data!")
            self.logger.exception(excep)
            return excep.message

    @cherrypy.expose
    @handle_error(redirect=False)
    @check_user
    def updatedata(self, **data):

        try:
            print(data)
            string = ''
            nodedict={}
            for k,v in data.items():
                if k not in self.dictComponentInfo.keys():
                    string += k.title() +':' + v + '  '
                    nodedict[k]=v

            #store the element without structure
            self.dictEsencial[self.userID][data['id']] = nodedict
            self.dictAll[self.userID][data['id']] = data

            #store elements ids with structure, later we consult the dictAll for properties of each element
            if(data['parent'] == 'none'):
                self.dictStructuredIDs[self.userID][data['id']] = []
            else:
                self.dictStructuredIDs[self.userID][data['parent']] = self.dictStructuredIDs[self.userID][data['parent']] + [data['id']]

            return data['type']+'-> '+data['name']+'(id:'+data['id']+')'

        except ServicesBaseException as excep:
            self.logger.error("Could not execute MetaData update!")
            self.logger.exception(excep)
            common.set_error_message(excep.message)
            return excep.message

    @expose_fragment("overlay")
    def details_model_overlay(self,nodeId, component_name, parent):
        template_specification={}
        param = {'parent': parent, 'type': component_name, 'id': nodeId}
        template_specification["nodeFields"] = dict(self.dictComponentType[component_name], **param)
        template_specification["noVisibleFields"] =  self.dictComponentInfo.keys()
        template_specification = self.fill_overlay_attributes(template_specification, "Setting parameters", nodeId,
                                                              "tools/details_model_overlay","dialog-upload")

        return self.fill_default_attributes(template_specification)

    @expose_page
    @settings
    def index(self, create=False, page=1, selected_project_id=None, **_):
        if cherrypy.request.method == 'POST' and create:
            raise cherrypy.HTTPRedirect('/tools/dsl/dsl_create')

        template_specification = dict(mainContent="tools/dsl_viewall", title="RateML Framework", mylista=self.xml_components)
        return self.fill_default_attributes(template_specification)

    @expose_page
    @settings
    def dsl_create(self, create=False, cancel=False, save=False, delete=False, convert=False,**data):

        if cherrypy.request.method == 'POST' and cancel:
            raise cherrypy.HTTPRedirect('/tools/dsl')
        if cherrypy.request.method == 'POST' and delete:
            raise cherrypy.HTTPRedirect('/tools/dsl')
        try:
            if cherrypy.request.method == 'POST' and save:
                #TODO Store the object
                raise cherrypy.HTTPRedirect('/tools/dsl')

        except Exception as excep:
            self.logger.debug(str(excep))
            common.set_error_message(excep.message)
            print(str(excep))
            raise cherrypy.HTTPRedirect('/tools/dsl')

        template_specification = dict(mainContent="tools/dsl_create", title="RateML Framework",
                                      mylista=self.xml_components)
        return self.fill_default_attributes(template_specification)


    def fill_default_attributes(self, template_dictionary):
        """
        Overwrite base controller to add required parameters for adapter templates.
        """
        template_dictionary[common.KEY_SECTION] = 'tools'
        template_dictionary[common.KEY_SUB_SECTION] = 'RateML'
        template_dictionary[common.KEY_SUBMENU_LIST] = self.submenu_list

        ToolsController.fill_default_attributes(self, template_dictionary)
        return template_dictionary

    def generateXML(self):

        try:
            lems = Xml.Element("Lems", attrib=self.dictModelInfo[self.userID])
            for key_layer1,val_layer1 in self.dictStructuredIDs[self.userID].items():

                comp = Xml.SubElement(lems, self.dictAll[self.userID][key_layer1]['type'], attrib=self.dictEsencial[self.userID][key_layer1])

                for item_id in val_layer1:
                    Xml.SubElement(comp, self.dictAll[self.userID][item_id]['type'], attrib=self.dictEsencial[self.userID][item_id])

            #Build the tree object
            tree = Xml.ElementTree(lems)

            #Store the XML file
            filepath = os.path.join(self.basepath, self.dictModelInfo[self.userID]['name']+'.xml')
            tree.write(filepath)
            print("Generated XML file!")
            print(filepath)

            lan_string = ''
            if self.dictModelInfo[self.userID]['language'].lower() == 'cuda':
                lan_string = 'CUDA'
            elif self.dictModelInfo[self.userID]['language'].lower() == 'python':
                lan_string = 'Python'
            print("Generating model in " + lan_string +" ...")

            #Todo Calling the Framework RateML
            #CodeGenerator.regTVB_templating(self.dictModelInfo[self.userID]['name'], basepath)

        except Exception as excep:
            self.logger.debug(str(excep))
            print(str(excep))