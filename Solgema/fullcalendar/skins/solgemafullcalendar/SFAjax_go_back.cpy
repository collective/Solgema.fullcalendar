## Controller Script (Python) "SFAjax_go_back.cpy"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=javascript=None
##title=Go back
##
REQUEST = context.REQUEST

# Tell the world that we cancelled
lifecycle_view = context.restrictedTraverse('@@at_lifecycle_view')
lifecycle_view.cancel_edit()

if not javascript:
    return state.set(status='success', next_action='redirect_to:string:SFAjax_base_cancel')

