[main]
host = https://www.transifex.com

[geomapfish.c2cgeoportal_geoportal-${tx_version.strip()}]
type = PO
source_file = geoportal/c2cgeoportal_geoportal/locale/c2cgeoportal_geoportal.pot
source_lang = en
% for lang in tx_languages.split():
trans.${lang} = geoportal/c2cgeoportal_geoportal/locale/${lang}/LC_MESSAGES/c2cgeoportal_geoportal.po
% endfor

[geomapfish.c2cgeoportal_admin-${tx_version.strip()}]
type = PO
source_file = admin/c2cgeoportal_admin/locale/c2cgeoportal_admin.pot
source_lang = en
% for lang in tx_languages.split():
trans.${lang} = admin/c2cgeoportal_admin/locale/${lang}/LC_MESSAGES/c2cgeoportal_admin.po
% endfor

[ngeo.gmf-apps-${tx_version.strip()}]
type = PO
source_lang = en
% for lang in tx_languages.split():
trans.${lang} = geoportal/c2cgeoportal_geoportal/scaffolds/create/geoportal/+package+_geoportal/locale/${lang}/LC_MESSAGES/+package+_geoportal-client.po
% endfor

[ngeo.ngeo-${tx_version.strip()}]
source_lang = en
type = PO
% for lang in tx_languages.split():
trans.${lang} = geoportal/c2cgeoportal_geoportal/locale/${lang}/LC_MESSAGES/ngeo.po
% endfor

[ngeo.gmf-${tx_version.strip()}]
source_lang = en
type = PO
% for lang in tx_languages.split():
trans.${lang} = geoportal/c2cgeoportal_geoportal/locale/${lang}/LC_MESSAGES/gmf.po
% endfor
