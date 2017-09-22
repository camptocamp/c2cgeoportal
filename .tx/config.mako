[main]
host = https://www.transifex.com

[geomapfish.c2cgeoportal-${tx_version.strip()}]
type = PO
source_file = c2cgeoportal/locale/c2cgeoportal.pot
source_lang = en
trans.de = c2cgeoportal/locale/de/LC_MESSAGES/c2cgeoportal.po
trans.fr = c2cgeoportal/locale/fr/LC_MESSAGES/c2cgeoportal.po

[ngeo.gmf-apps-${tx_version.strip()}]
type = PO
source_lang = en
trans.de = c2cgeoportal/scaffolds/create/+package+/locale/de/LC_MESSAGES/+package+-client.po
trans.fr = c2cgeoportal/scaffolds/create/+package+/locale/fr/LC_MESSAGES/+package+-client.po

[ngeo.ngeo-${tx_version.strip()}]
source_lang = en
type = PO
% for lang in ngeo_tx_languages:
trans.${lang} = /opt/locale/${lang}/LC_MESSAGES/ngeo.po
% endfor

[ngeo.gmf-${tx_version.strip()}]
source_lang = en
type = PO
% for lang in ngeo_tx_languages:
trans.${lang} = /opt/locale/${lang}/LC_MESSAGES/gmf.po
% endfor
