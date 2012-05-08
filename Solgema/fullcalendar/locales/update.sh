domain=Solgema.fullcalendar
../../../../../../Python-2.6/bin/i18ndude rebuild-pot --pot $domain.pot --create $domain ../
../../../../../../Python-2.6/bin/i18ndude sync --pot $domain.pot */LC_MESSAGES/$domain.po

#i18ndude rebuild-pot --pot plone.pot --merge plone-manual.pot --create plone ../profiles
../../../../../../Python-2.6/bin/i18ndude sync --pot plone-manual.pot ../i18n/Solgema-plone-*.po
