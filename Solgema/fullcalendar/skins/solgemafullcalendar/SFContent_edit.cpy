## Controller Script (Python) "SFContent_edit.cpy"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=id=''
##title=Edit Content for Solgema.fullcalendar
##
last_referer = context.REQUEST.get('last_referer', '')
state = context.content_edit_impl(state, id)
return state.set(last_referer=last_referer)
