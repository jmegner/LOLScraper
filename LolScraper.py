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
LolScraperVersion = "0.02"


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
            entryTexts = [elem.string.replace(",","").strip() for elem
                in row.contents if elem is not None and elem.string is not None]

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

    summonerListFile.close()

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


