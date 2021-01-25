import cherrypy, os, json, glob

from tvb.rateML.XML2model import RateML
from tvb.basic.profile import TvbProfile
from tvb.basic.logger.builder import get_logger
from tvb.core.services.exceptions import ServicesBaseException
from tvb.core.services.operation_service import OperationService
from tvb.interfaces.web.controllers import common
from tvb.interfaces.web.controllers.decorators import expose_page, using_template, settings, expose_fragment, \
    handle_error, check_user
from tvb.interfaces.web.controllers.tools.tools_controller import ToolsController
import xml.etree.cElementTree as Xml

from lxml import etree

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
        #self.basepath = os.path.join(os.getenv("HOME"),'tvb_temporal_folder')
        self.basepath = TvbProfile.current.TVB_TEMP_FOLDER #"/home/aaron/TVB/TEMP"
        self.xml_model_location = dict()
        self.xml_model_location["user"] = self.basepath
        self.xml_model_location["tvb"] = TvbProfile.current.TVB_STORAGE
        self.xml_namespaces = dict()
        #self.xml_namespaces['xmlns'] = "file://" + os.path.join(self.basepath,"rML_v0.xsd")
        self.xml_namespaces['xmlns:xsi'] = "http://www.w3.org/2001/XMLSchema-instance"
        #self.xml_namespaces['xsi:schemaLocation'] = "file://" + os.path.join(self.basepath,"rML_v0.xsd")

        #self.xsd_validator_file = "file://" + os.path.join(self.basepath,"rML_v0.xsd")
        self.xml_components = dict()
        self.xml_components["python"] = {"ComponentType": "",
                                         "Constant": "ComponentType",
                                         "Exposure": "ComponentType",
                                         "Dynamics": "ComponentType",
                                         "StateVariable": "Dynamics",
                                         "DerivedVariable": "Dynamics",
                                         "TimeDerivative": "Dynamics"}
        self.xml_components["cuda"] = {"ComponentType": "",
                                         "Constant": "ComponentType",
                                         "Exposure": "ComponentType",
                                         "Parameter": "ComponentType",
                                         "DerivedParameter": "ComponentType",
                                         "Dynamics": "ComponentType",
                                         "StateVariable": "Dynamics",
                                         "DerivedVariable": "Dynamics"}

        #ComponentType
        # - constant
        # - Dynamic
        #    - Variable

        self.dictComponentInfo = {'id': '', 'type': '', 'parent': ''}

        # TODO: get dynamically from LEMS
        self.dictComponentType = dict()
        self.dictComponentType["python"] = {"ComponentType": {'name': '', 'description': ''},
                                            "Constant": {'name': '', 'dimension': '', 'value': '', 'description': ''},
                                            "Exposure": {'name': '', 'dimension': '', 'description': ''},
                                            "Dynamics": {'name': ''},
                                            "StateVariable": {'name': '', 'dimension': '', 'exposure': ''},
                                            "DerivedVariable": {'name': '', 'value': ''},
                                            "ConditionalDerivedVariable": {'name': '', 'cases': '', 'dimension': ''},
                                            "TimeDerivative": {'variable': '', 'value': ''}
                                            }
        self.dictComponentType["cuda"] = {"ComponentType": {'name': '', 'description': ''},
                                            "Constant": {'name': '', 'dimension': '', 'value': '', 'description': ''},
                                            "Exposure": {'name': '', 'dimension': '', 'description': ''},
                                            "Parameter": {'name': '', 'dimension': ''},
                                            "DerivedParameter": {'name': '', 'dimension': '', 'value': ''},
                                            "Dynamics": {'name': ''},
                                            "StateVariable": {'name': '', 'dimension': '', 'exposure': ''},
                                            "DerivedVariable": {'name': '', 'value': ''},
                                            "ConditionalDerivedVariable": {'name': '', 'cases': '', 'dimension': ''},
                                            "TimeDerivative": {'variable': '', 'value': ''}
                                            }

        '''
        self.dictComponentType["python"] = {"ComponentType": {'name': '', 'description': ''},
                                    "Constant": {'name': '', 'domain': '', 'default': '', 'description': ''},
                                    "Exposure": {'name': '', 'choices': '', 'default': '', 'description': ''},
                                "Dynamics": {'name': ''},
                                    "StateVariable": {'name': '', 'default': '', 'boundaries': ''},
                                    "DerivedVariable": {'name': '', 'expression': ''},
                                    "ConditionalDerivedVariable": {'name': '', 'cases': '', 'condition': ''},
                                    "TimeDerivative": {'name': '', 'expression': ''}
                                }
        # ComponentType , 'value': ''
        self.dictComponentType["cuda"] ={"ComponentType": {'name': '', 'description': ''},
                                            "Constant": {'name': '', 'domain': '', 'default': '', 'description': ''},
                                            "Exposure": {'name': '', 'choices': '', 'default': ''},
                                            "Parameter": {'name': '', 'dimension': ''},
                                            "DerivedParameter": {'name': '', 'expression': '', 'value': ''},
                                         "Dynamics": {'name': ''},
                                            "StateVariable": {'name': '', 'default': '', 'boundaries': ''},
                                            "DerivedVariable": {'name': '', 'expression': ''},
                                            "ConditionalDerivedVariable": {'name': '', 'cases': '', 'condition': ''},
                                            "TimeDerivative": {'name': '', 'expression': ''},
                                         }
        '''

        #TODO: get the session id
        self.userID = 20

        self.resetdictionaries();

    def resetdictionaries(self):
        self.dictAll[self.userID] = {}
        self.dictEsencial[self.userID] = {}
        self.dictStructuredIDs[self.userID] = {}
        self.dictModelInfo[self.userID] = {}

    @cherrypy.expose
    @handle_error(redirect=False)
    @check_user
    def getComponents(self, param):
        try:
            if len(str(param)) > 0:
                return json.dumps(self.xml_components[str(param).lower()])
        except Exception as excep:
            self.logger.error("No data to provide! ", excep)

    @cherrypy.expose
    @handle_error(redirect=False)
    @check_user
    def getxml(self, **data):
        try:
            for key, value in data.items():
                if(len(key) > 0):
                    self.dictModelInfo[self.userID][key] = value

            stored, filename = self.generateXML(self.dictModelInfo[self.userID]['language'])
            loaded, content = self.getXMLContent(filename)
            if stored and loaded:
                return content
            else:
                return ""
        except Exception as excep:
            self.logger.error("Could not convert data! ", excep)

    @cherrypy.expose
    @handle_error(redirect=False)
    @check_user
    def getmodels(self, **data):
        try:
            for key, value in data.items():
                if (len(key) > 0):
                    self.dictModelInfo[self.userID][key] = value
            files = []
            if(len(data["model_location_option"])>0):

                folder = self.xml_model_location[data["model_location_option"]]
                for filename in glob.glob(os.path.join(folder,"*")):
                    if(os.path.isfile(filename)):
                        path, extension =os.path.splitext(filename)
                        if extension.lower() == ".xml":
                            files.append(filename.split(os.path.sep)[-1])

                return json.dumps({"folder":folder, "files":files})
            else:
                return json.dumps({"folder":"", "files":""})
        except Exception as excep:
            self.logger.error("Could not convert data! ", excep)
    @cherrypy.expose
    @handle_error(redirect=False)
    @check_user
    def convertdata(self, **data):
        try:
            for key, value in data.items():
                if(len(key) > 0):
                    self.dictModelInfo[self.userID][key] = value

            validation, msg = self.createXML(self.dictModelInfo[self.userID]['language'])
            if validation:
                return "Converted file!"
            else:
                return "Could not convert data! \n" + msg

        except Exception as excep:
            self.logger.error("Could not convert data! ", excep)

    @cherrypy.expose
    @handle_error(redirect=False)
    @check_user
    def convertmodel_findall(self, **data):
        try:
            dict = {}
            for key, value in data.items():
                if(len(key) > 0):
                    dict[key] = value
            filename, extension = os.path.splitext(dict["model_name"])

            rateml = RateML(model_filename=filename,
                            language=dict["model_language"].lower(),
                            XMLfolder=self.xml_model_location[dict["model_location_option"]],
                            GENfolder=self.xml_model_location[dict["model_location_option"]])
            finished, validation = rateml.transform()
            if finished:
                content = ""
                with open(rateml.generated_model_location, 'r') as content_file:
                    content = content_file.read()
                return content
            else:
                raise validation

        except Exception as excep:
            return "Could not convert data! "

    @cherrypy.expose
    @handle_error(redirect=False)
    @check_user
    def updatedata(self, **data):

        try:
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
    def details_model_overlay(self,language, nodeId, component_name, parent):
        template_specification={}
        param = {'parent': parent, 'type': component_name, 'id': nodeId}
        template_specification["nodeFields"] = dict(self.dictComponentType[language][component_name], **param)
        template_specification["noVisibleFields"] =  self.dictComponentInfo.keys()
        template_specification = self.fill_overlay_attributes(template_specification, "Setting parameters", component_name +" for " + language + " Models.",
                                                              "tools/details_model_overlay","dialog-upload")

        return self.fill_default_attributes(template_specification)

    @expose_page
    @settings
    def index(self, create=False, page=1, selected_project_id=None, **_):
        self.dictModelInfo[self.userID] = {}

        if cherrypy.request.method == 'POST' and create:
            raise cherrypy.HTTPRedirect('/tools/dsl/dsl_create')

        template_specification = dict(mainContent="tools/dsl_viewall", title="RateML Framework", selectedOptions="")#,
        #                              mylista=self.xml_components, selectedOptions="cuda")
        self.resetdictionaries();
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
            self.logger.error(str(excep))
            raise cherrypy.HTTPRedirect('/tools/dsl')

        template_specification = dict(mainContent="tools/dsl_create", title="RateML Framework", selectedOptions="")#,
        #                              mylista=self.xml_components, selectedOptions="cuda")

        self.resetdictionaries();
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

    def getXMLContent(self,filename):
        try:
            content = etree.parse(filename)
            return True, etree.tostring(content, pretty_print=True).decode('utf-8')

        except Exception as excep:
            self.logger.error(str(excep))
            return False, str(excep)

    # Structured data
    # { Component:{ SubComponent_1:{}, Subcomponent_2:{}, Subcomponent_3:{Sub-subComponen1: {} } } }
    def generateXML(self, language):
        try:
            #lems = Xml.Element("Lems", attrib=self.xml_namespaces)#, attrib=self.dictModelInfo[self.userID]

            lems = Xml.Element("Lems")
            for key_layer1, val_layer1 in self.dictStructuredIDs[self.userID].items():

                # Principal component
                comp = Xml.SubElement(lems, self.dictAll[self.userID][key_layer1]['type'],
                                      attrib=self.dictEsencial[self.userID][key_layer1])

                # Subcomponents
                for key_layer2, val_layer2 in val_layer1.items():
                    subcomponent = self.dictAll[self.userID][key_layer2]['type']

                    if subcomponent == "Dynamics":
                        sub = Xml.SubElement(comp, subcomponent)
                    else:
                        sub = Xml.SubElement(comp, subcomponent,
                                             attrib=self.dictEsencial[self.userID][key_layer2])
                    #if(key_layer2 == "Dynamics"):
                    #    #Dynamics does not contain attributes, just subcomponents
                    #    sub = Xml.SubElement(comp, self.dictAll[self.userID][key_layer2]['type'],
                    #                         attrib=self.dictEsencial[self.userID][key_layer2])
                    #else:
                    #
                    #    sub = Xml.SubElement(comp, self.dictAll[self.userID][key_layer2]['type'])

                    # Sub-Subcomponents
                    for key_layer3, val_layer3 in val_layer2.items():
                            Xml.SubElement(sub, self.dictAll[self.userID][key_layer3]['type'],
                                           attrib=self.dictEsencial[self.userID][key_layer3])

            # Build the tree object
            tree = Xml.ElementTree(lems)

            # Store the XML file
            """
            filepath = ""
            if (self.dictModelInfo[self.userID]['language'].lower() == 'cuda'):
                filepath = os.path.join(self.basepath, self.dictModelInfo[self.userID]['name'] + '_CUDA.xml')
            elif (self.dictModelInfo[self.userID]['language'].lower() == 'python'):
                filepath = os.path.join(self.basepath, self.dictModelInfo[self.userID]['name'] + '.xml')
            else:
                raise ("No Programing language implemented!")
            """
            filepath = os.path.join(self.basepath, self.dictModelInfo[self.userID]['name'] + '.xml')
            tree.write(filepath)

            exist, content = self.getXMLContent(filepath)
            if exist:
                with open(filepath, "w") as writter:
                    writter.write(content)

            return True, filepath
        except Exception as excep:
            self.logger.error(str(excep))
            return False, str(excep)

    def convertXML(self, language, xmlmodel, outputfolder):
        finished = False
        try:
            xmlfolder, filename = path.split(xmlmodel)
            rateml = RateML(model_filename=filename,
                            language=language,
                            XMLfolder=xmlfolder,  # XMLfolder="./XMLmodels/",
                            GENfolder=outputfolder)
            finished, validation = rateml.transform()
            if finished:
                return True, "Generated model in " + language
            else:
                return finished, validation

        except Exception as excep:
            self.logger.error(str(excep))


    def createXML(self, language):
        finished=False
        validation=""
        try:
            file_stored, file_msg = self.generateXML(language)
            if not file_stored:
                raise("No XML file generated!")

            lang = self.dictModelInfo[self.userID]['language'].lower()
            rateml = RateML(model_filename=self.dictModelInfo[self.userID]['name'],
                            language=lang,
                            XMLfolder=os.path.dirname(os.path.abspath(file_msg)),#XMLfolder="./XMLmodels/",
                            GENfolder=self.basepath)
            finished, validation = rateml.transform()
            if finished:
                return True, "Generated model in "+lang
            else:
                return finished, validation

        except Exception as excep:
            self.logger.error(str(excep))
            return False, "Internal exception \n" + str(excep)