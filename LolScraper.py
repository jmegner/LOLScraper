#! /usr/bin/env python
"""
initial author:   Jacob Egner
initial date:     2012-01-06

"""


import sys
import getopt
import re
#import collections
#import math
#import time
import urllib2
from BeautifulSoup import BeautifulSoup # for processing HTML
import codecs


global LolScraperVersion
LolScraperVersion = "0.01"


################################################################################
# SkewFieldLetter is an alphabetical identifier and a subscript
# this representation can neither be a zero nor a one
#
# example: b_1
#   'b' is the alpha
#   '1' is the sub
#
class SkewFieldLetter():

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], str):
            #match = re.match("^([a-z]+)_?(-?\d*)$", args[0].replace(" ", ""))
            components = args[0].split("_")

            if len(components) != 2:
                raise ValueError("bad SkewFieldLetter() args " + str(args))

            self.alpha = SkewFieldLetter.alphaAsInt(components[0])
            self.sub = int(components[1])
        elif len(args) == 2:
            self.alpha = SkewFieldLetter.alphaAsInt(args[0])
            self.sub = int(args[1])
        else:
            raise ValueError("bad SkewFieldLetter() args " + str(args))


    def __str__(self):
        return SkewFieldLetter.alphaAsStr(self.alpha) + "_" + str(self.sub)


    def __repr__(self):
        return "SkewFieldLetter(\"" + str(self) + "\")"


    def __hash__(self):
        # imagine alpha as a row index and sub as a col index
        # and we're using the bijection of an infinite 2d array into an
        # infinite 1d array by traversing the 2d array diagonally;
        # this way our hash function is good at generating unique 1-tuples for
        # any combination of the alpha-sub 2-tuples

        #r = self.alpha
        #c = self.sub
        #return c * (c + 1) // 2 + r * c + r * (r + 1) // 2 + r

        # or we could go for this more efficient guy for sake of performance
        hashVal = self.sub * 128 + self.alpha + 1

        if hashVal == -1:
            return -2

        return hashVal


    def __eq__(self, other):
        if self.alpha != other.alpha:
            return False
        return self.sub == other.sub


    def __cmp__(self, other):
        if self.alpha < other.alpha:
            return -1
        if self.alpha > other.alpha:
            return 1
        if self.sub < other.sub:
            return -1
        if self.sub > other.sub:
            return 1
        return 0


    def deepcopy(self):
        return SkewFieldLetter(self.alpha, self.sub)


    @staticmethod
    def alphaAsInt(alpha):
        if isinstance(alpha, int):
            return alpha
        elif isinstance(alpha, str):

            if re.match("^[a-z]+$", alpha) is None:
                raise ValueError("can not use arg " + str(alpha))

            intRep = -1;
            for char in alpha:
                intRep = (intRep + 1) * 26 + (ord(char) - ord("a"))

            return intRep

        else:
            raise ValueError("can not use arg " + str(alpha))


################################################################################
# BLAH
################################################################################


def LolScraperMain(argv=None):

    cprint = noPrint

    if not(argv is None) and len(argv) > 1:
        for arg in argv[1:]:
            if arg == "-v" or arg == "--verbose":
                cprint = yesPrint

    print("LolScraper.py Version = " + LolScraperVersion)

    regions = ["na", "euw", "eune", ]

    for region in regions:
        getDataForRegion(region)

    return 0


def getDataForRegion(region):

    summonerListFile = codecs.open(
        "summoner_list." + region + ".csv",
        encoding = "utf-8",
        mode = "w")

    pageNum = 0

    while True:

        pageUrl = ("http://competitive." + region
            + ".leagueoflegends.com/ladders/" + region
            + "/current/rankedsolo5x5?page="
            + str(pageNum)
            )

        page = urllib2.urlopen(pageUrl)

        parseTree = BeautifulSoup(page)
        removeWhitespaceContents(parseTree)

        rankingTables = parseTree.findAll("table", {"class" : "views-table cols-6"})

        # check we got exactly one ranking table on the page
        if len(rankingTables) != 1:
            raise ValueError("got " + str(len(rankingTables))
                + " possible ranking tables on page;"
                + " was expecting 1 possible ranking table")

        rankingTable = rankingTables[0]

        # further checks that we got the right table

        if rankingTable.thead is None:
            raise ValueError("ranking table did not have thead element")

        if rankingTable.thead.tr is None:
            raise ValueError("ranking table header did not have tr element")

        columnTitles = [str(thElem.string.strip()) for thElem
            in rankingTable.thead.tr.contents if thElem.string is not None]

        if len(columnTitles) != 5 :
            raise ValueError("weird number of column titles")

        # put column titles if on first page
        if pageNum == 0 :

            summonerListFile.write(",".join(columnTitles) + "\n")

        bodyRows = rankingTable.tbody.contents

        if bodyRows is None or len(bodyRows) == 0 or bodyRows[0].name != "tr" :
            raise ValueError("ranking table body rows were weird")

        for row in bodyRows:
            entryTexts = [elem.string.strip() for elem in row.contents
                if elem is not None and elem.string is not None]

            if len(columnTitles) != len(entryTexts) :
                raise ValueError("weird number of entry texts in ranking table body row")

            summonerListFile.write(",".join(entryTexts) + "\n")

        # if no link to go to last page, we must be at last page
        lastPagers = parseTree.findAll("li", {"class" : "pager-last last"})

        if len(lastPagers) == 0 :
            print("done with region " + region)
            break
        else:
            lastPageNum = int(lastPagers[0].a["href"].split("=")[2])

        print("finished region=" + region + " page=" + str(pageNum) + "/"
            + str(lastPageNum))

        pageNum += 1

    return 0


def noPrint(arg):
    pass


def yesPrint(arg):
    print(arg)


def removeWhitespaceContents(parseTree):
    elem = parseTree.contents[0]

    while True:
        if elem is None:
            break
        if elem.previous == u'\n' :
            elem.previous.extract()
        elem = elem.next


if __name__ == "__main__":
    sys.exit(LolScraperMain(sys.argv))


