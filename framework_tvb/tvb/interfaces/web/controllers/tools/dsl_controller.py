import cherrypy, os
import tvb
from tvb.dsl.LEMS2python import regTVB_templating
from tvb.dsl.NeuroML.lems.parser.LEMS import LEMSFileParser
from tvb.basic.logger.builder import get_logger
from tvb.core.services.exceptions import ServicesBaseException
from tvb.core.services.operation_service import OperationService
from tvb.interfaces.web.controllers import common
from tvb.interfaces.web.controllers.decorators import expose_page, using_template, settings, expose_fragment, \
    handle_error, check_user
from tvb.interfaces.web.controllers.tools.tools_controller import ToolsController
import xml.etree.cElementTree as Xml

def check_LEM_file(filename, path):
    try:
        print("Go!")
        #path=['/home/aaron/projects/gui-cuda-dsl/tvb-root/tvb-root/scientific_library/tvb/dsl/NeuroML/XMLmodels']

        filepath = os.path.join(path, 'modelito.xml')
        path = [path]
        parser = LEMSFileParser(model=filename,include_dirs=path,include_includes=True)
        #filepath = os.path.join(path, filename.lower() + '.xml')


        print("test",path)
        print("test",filepath)

        print("Validating ->",filepath)
        with open(filepath) as f:
            print("Validating ->", "IN1")
            parser.parse(f.read())
            print("Validating ->", "IN2")
            print("Validation Ok")
    except Exception as ex:
        print(ex)


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

        self.xml_components={"ComponentType": "",
         "Constant": "ComponentType",
         "Exposure": "ComponentType",
         "Dynamics": "ComponentType",
         "StateVariable": "Dynamics",
         "DerivedVariable": "Dynamics",
         "TimeDerivative": "Dynamics"}

        #ComponentType
        # - constant
        # - Dynamic
        #    - Variable

        self.dictComponentInfo = {'id': '', 'type': '', 'parent': ''}

        # TODO: get dynamically from LEMS
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
            if(self.generateXML()):
                return "Converted file!"

        except Exception as excep:
            self.logger.error("Could not convert data! ", excep)

        return "Could not convert data!"

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

            #store the element without structure but with all properties
            self.dictEsencial[self.userID][data['id']] = nodedict
            self.dictAll[self.userID][data['id']] = data

            #store elements ids with structure, later we consult the dictAll for properties of each element
            # Structured data
            # { Component:{ SubComponent_1:{}, Subcomponent_2:{}, Subcomponent_3:{Sub-subComponen1: {} } } }

            # New principal component
            if int(data["parent"]) == 0:
                self.dictStructuredIDs[self.userID][data['id']] = {}

            # New Subcomponent
            else:
                newDict = {}
                newDict[data['id']] = {}

                found = False
                #Finding if a its parent has parent as well
                for k1,v1 in self.dictStructuredIDs[self.userID].items():
                    for k2,v2 in self.dictStructuredIDs[self.userID][k1].items():
                        if k2 == data['parent']:
                            self.dictStructuredIDs[self.userID][k1][data['parent']].update(newDict)
                            found = True
                            break

                if not found:
                    self.dictStructuredIDs[self.userID][data['parent']][data['id']] = {}

            # Name for the TreeNode
            return data['type']+'-> '+data['name']+'(id:'+data['id']+')'

        except ServicesBaseException as excep:
            self.logger.error("Could not execute MetaData update!")
            self.logger.exception(excep)
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

    # Structured data
    # { Component:{ SubComponent_1:{}, Subcomponent_2:{}, Subcomponent_3:{Sub-subComponen1: {} } } }
    def generateXML(self):

        try:
            lems = Xml.Element("Lems", attrib=self.dictModelInfo[self.userID])
            for key_layer1,val_layer1 in self.dictStructuredIDs[self.userID].items():

                # Principal component
                comp = Xml.SubElement(lems, self.dictAll[self.userID][key_layer1]['type'], attrib=self.dictEsencial[self.userID][key_layer1])

                # Subcomponents
                for key_layer2, val_layer2 in val_layer1.items():
                    print("key2:", key_layer2, "value2:", val_layer2)

                    sub = Xml.SubElement(comp, self.dictAll[self.userID][key_layer2]['type'],
                                   attrib=self.dictEsencial[self.userID][key_layer2])

                    # Sub-Subcomponents
                    for key_layer3, val_layer3 in val_layer2.items():
                        print("key3:", key_layer3, "value3:", val_layer3)
                        Xml.SubElement(sub, self.dictAll[self.userID][key_layer3]['type'],
                                             attrib=self.dictEsencial[self.userID][key_layer3])

            #Build the tree object
            tree = Xml.ElementTree(lems)

            #Store the XML file
            filepath = os.path.join(self.basepath, self.dictModelInfo[self.userID]['name']+'.xml')
            tree.write(filepath)
            print("Generated XML file!")
            print(filepath)

            if self.dictModelInfo[self.userID]['language'].lower() == 'cuda':
                # Todo Calling the Framework DSL_CUDA
                print("Functionality Not implemented!")

            elif self.dictModelInfo[self.userID]['language'].lower() == 'python':
                # Calling the RateML Framework
                print("Generating model in Python ...", self.dictModelInfo[self.userID]['name'])
                return regTVB_templating(self.dictModelInfo[self.userID]['name'], self.basepath)

        except Exception as excep:
            self.logger.debug(str(excep))
            print(str(excep))

        return False