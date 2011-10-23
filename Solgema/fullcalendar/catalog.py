from plone.indexer.decorator import indexer
from zope.interface import Interface
from AccessControl.PermissionRole import rolesForPermissionOn
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CatalogTool import _mergedLocalRoles
from interfaces import ISFBaseEventFields
from zope.annotation.interfaces import IAttributeAnnotatable

@indexer(Interface)
def SFAllowedRolesAndUsersModify(obj):
    """Return a list of roles and users with Modify portal content permission.
    Used by PortalCatalog to filter out items you're not allowed to modify in the calendar.
    """
    allowed = {}
    for r in rolesForPermissionOn('Modify portal content', obj):
        allowed[r] = 1
    try:
        acl_users = getToolByName(obj, 'acl_users')
        localroles = acl_users._getAllLocalRoles(obj)
    except AttributeError:
        localroles = _mergedLocalRoles(obj)

    for user, roles in localroles.items():
        for role in roles:
            if allowed.has_key(role):
                allowed['user:' + user] = 1
    if allowed.has_key('Owner'):
        del allowed['Owner']
    return list(allowed.keys())

@indexer(IAttributeAnnotatable)
def SFAllDay(obj):
    adapted = ISFBaseEventFields(obj, None)
    if adapted is not None:
        return adapted.allDay
    return None
