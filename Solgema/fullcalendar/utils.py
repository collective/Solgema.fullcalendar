
# Check for plone.(app.)uuid, conditional uid getter with fallback
try:
    from plone.uuid.interfaces import IUUID
    import plone.app.uuid
    get_uid = lambda o: IUUID(o, None)
except ImportError:
    get_uid = lambda o: o.UID()
