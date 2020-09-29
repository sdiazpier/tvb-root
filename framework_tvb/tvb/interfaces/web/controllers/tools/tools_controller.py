from tvb.basic.logger.builder import get_logger
from tvb.core.adapters.abcadapter import ABCAdapter
from tvb.core.entities.model.model_burst import PARAM_SURFACE
from tvb.core.neocom import h5
from tvb.core.services.operation_service import OperationService
from tvb.interfaces.web.controllers import common
from tvb.interfaces.web.controllers.autologging import traced
from tvb.interfaces.web.controllers.base_controller import BaseController
from tvb.interfaces.web.controllers.common import MissingDataException
from tvb.interfaces.web.controllers.decorators import settings, expose_page, using_template


@traced
class ToolsController(BaseController):
    """
    This class contains the methods served at the root of the Web site.
    """

    def __init__(self):
        BaseController.__init__(self)
        self.logger = get_logger(__name__)
        editable_entities = [dict(link='/tools/dsl', title='RateML Model Generator',
                                  description='Create your model with the RateML Framework')]
        self.submenu_list = editable_entities

    @expose_page
    @settings
    def index(self, **data):
        """
        / Path response
        Redirects to /tvb
        """
        template_specification = {'title': "Advanced tools for Neuroscience", 'data': data, 'mainContent': 'header_menu'}
        return self.fill_default_attributes(template_specification)

    def fill_default_attributes(self, template_dictionary):
        """
        Overwrite base controller to add required parameters for adapter templates.
        """
        template_dictionary[common.KEY_SECTION] = 'tools'
        template_dictionary[common.KEY_SUBMENU_LIST] = self.submenu_list
        BaseController.fill_default_attributes(self, template_dictionary)
        return template_dictionary

    @using_template('/tools/base_tools')
    def render_tools_form(self, adatp_form):
        return adatp_form.get_rendering_dict()

