domain=Solgema.fullcalendar
i18ndude rebuild-pot --pot $domain.pot --create $domain ../
i18ndude sync --pot $domain.pot */LC_MESSAGES/$domain.po

#i18ndude rebuild-pot --pot plone.pot --merge plone-manual.pot --create plone ../profiles
i18ndude sync --pot plone-manual.pot ../i18n/Solgema-plone-*.po
