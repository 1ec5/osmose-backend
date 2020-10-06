#-*- coding: utf-8 -*-

###########################################################################
##                                                                       ##
## Copyrights Etienne Chové <chove@crans.org> 2009                       ##
##                                                                       ##
## This program is free software: you can redistribute it and/or modify  ##
## it under the terms of the GNU General Public License as published by  ##
## the Free Software Foundation, either version 3 of the License, or     ##
## (at your option) any later version.                                   ##
##                                                                       ##
## This program is distributed in the hope that it will be useful,       ##
## but WITHOUT ANY WARRANTY; without even the implied warranty of        ##
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         ##
## GNU General Public License for more details.                          ##
##                                                                       ##
## You should have received a copy of the GNU General Public License     ##
## along with this program.  If not, see <http://www.gnu.org/licenses/>. ##
##                                                                       ##
###########################################################################

from .Name_Dictionary import P_Name_Dictionary


class Name_Dictionary_Lang_fr(P_Name_Dictionary):

    only_for = ["fr"]

    def init(self, logger):
        P_Name_Dictionary.init(self, logger)

    def init_dictionaries(self):
        self.load_external_dictionaries('fr')
        self.laod_numbering()
        self.load_latin_language()

        # French

        # Roman numbers
        for i in [u"",u"X",u"XX"]:
            for j in [u"I",u"II",u"III",u"IV",u"V",u"VI",u"VII",u"VIII",u"IX",u"X"]:
                self.DictKnownWords.append(i + j)
                self.DictKnownWords.append(i + j + u"ème")
                self.DictKnownWords.append(i + j + u"è")
                self.DictKnownWords.append(i + j + u"e")
                self.DictKnownWords.append(i + j + u"ième")

        # Enurations
        self.DictKnownWords.append("1e")
        self.DictKnownWords.append("1er")
        for i in range(2,2000):
            self.DictKnownWords.append(u"{0}ème".format(i))
            self.DictKnownWords.append(u"{0}è".format(i))
            self.DictKnownWords.append(u"{0}e".format(i))
            self.DictKnownWords.append(u"{0}ième".format(i))

        for i in range(2,2000):
            self.DictCorrections[u"{0}ieme".format(i)] = u"{0}ième".format(i)
            self.DictCorrections[u"{0}eme".format(i)] = u"{0}ème".format(i)
            self.DictCorrections[u"{0}éme".format(i)] = u"{0}ème".format(i)
            #BadDict[u"{0}e".format(i)] = u"{0}è".format(i)

        # France

        # Dictionaries : Routes
        for i in range(0,2000):
            self.DictKnownWords.append(u"A{0}".format(i))
            self.DictKnownWords.append(u"D{0}".format(i))
            self.DictKnownWords.append(u"N{0}".format(i))
            self.DictKnownWords.append(u"C{0}".format(i))
            self.DictKnownWords.append(u"E{0}".format(i))
            self.DictKnownWords.append(u"RN{0}".format(i))


###########################################################################
from plugins.Plugin import TestPluginCommon

class Test(TestPluginCommon):
    def test(self):
        from analysers.analyser_sax import Analyser_Sax
        class _config:
            options = {"language": "fr"}
        class father(Analyser_Sax):
            config = _config()
            def __init__(self):
                pass
        a = Name_Dictionary_Lang_fr(father())
        a.init(None)
        assert not a.node(None, {"highway": "Pont des Anes"})
        name = [(u"Pont des Anes", u"Pont des Ânes"),
                (u"Pont des Ânes", None),
                (u"Rue Saint-AndrÃ©", u"Rue Saint-André"),
                (u"Rue Saint-André", None),
                (u"Rue de l`Acadie", u"Rue de l'Acadie"),
                (u"200ième rue", None),
                (u"199ème avenue", None),
                (u"199ème Avenude", u"199ème Avenue"),
                (u"199ème Avenue", None),
                (u"\u00c3\u0087a", u"Ça"),
                (u"Ça", None),
               ]
        for (n, f) in name:
            rdp = a.node(None, {"name": n})
            if f:
                self.check_err(rdp, ("name='{0}'".format(n)))
                fix = rdp[0]["fix"]["name"]
                self.assertEqual(fix, f, u"name='{0}' - fix = wanted='{1}' / got='{2}'".format(n, f, fix))
            else:
                assert not rdp, ("name='{0}'".format(n))

        assert not a.way(None, {"highway": u"Rue Saint-AndrÃ©"}, None)
        assert not a.relation(None, {"highway": u"Rue Saint-AndrÃ©"}, None)
        assert not a.way(None, {"name": u"Rue Saint-André"}, None)
        assert not a.relation(None, {"name": u"Rue Saint-André"}, None)
        self.check_err(a.way(None, {"name": u"Rue Saint-AndrÃ©"}, None))
        self.check_err(a.relation(None, {"name": u"Rue Saint-AndrÃ©"}, None))

        # code that is not reachable in normal cases
        import pytest
        a.DictCorrections["buebdgxrtsuei"] = None
        with pytest.raises(Exception):
            a.node({"name": "ceci est buebdgxrtsuei"})
