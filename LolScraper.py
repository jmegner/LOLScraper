#! /usr/bin/env python
"""
initial author:   Jacob Egner
initial date:     2012-01-06

"""


import sys
import getopt
import re
import math
import urllib2
from BeautifulSoup import BeautifulSoup # for processing HTML
import codecs
from collections import Counter
import bisect


global LolScraperVersion
LolScraperVersion = "0.03"


def LolScraperMain(argv=None):

    cprint = noPrint

    regions = list()

    if not(argv is None) and len(argv) > 1:
        for arg in argv[1:]:
            if arg == "-v" or arg == "--verbose":
                cprint = yesPrint
            elif arg[0] == "-" :
                raise ValueError("unrecognized flag %s" % arg)
            else:
                regions.append(arg)

    print("LolScraper.py Version = " + LolScraperVersion)

    if len(regions) == 0 :
        regions = ["na", "euw", "eune", ]

    for region in regions:
        getDataForRegion(region)

    return 0


def getDataForRegion(region):

    summonerListFile = codecs.open(
        filename = "summoner_list." + region + ".csv",
        encoding = "utf-8",
        mode = "w")

    pageNum = 0
    elos = list()

    while True:

        pageUrl = ("http://competitive." + region
            + ".leagueoflegends.com/ladders/" + region
            + "/current/rankedsolo5x5?page="
            + str(pageNum)
            )

        fetchAttempts = 0
        pageFetched = False
        page = None

        while fetchAttempts < 5 and not pageFetched:
            try:
                fetchAttempts += 1
                page = urllib2.urlopen(url = pageUrl)
                pageFetched = True
            except urllib2.URLError as fetchError:
                print("URLError=<%s>  pageUrl=%s" % (fetchError, pageUrl))

        if not pageFetched:
            print("giving up on region %s" % region)
            return False

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

        # look at the data in the ranking tables

        for row in bodyRows:
            # when getting text of row, drop all commas; they mess up csv files
            entryTexts = [elem.string.replace(",","").strip() for elem
                in row.contents if elem is not None and elem.string is not None]

            if len(columnTitles) != len(entryTexts) :
                raise ValueError("weird number of entry texts in ranking table body row")

            #rank      = int(entryTexts[0])
            #summoner  = entryTexts[1]
            #winCount  = int(entryTexts[2])
            #lossCount = int(entryTexts[3])
            #elo       = int(entryTexts[4])

            elos.append(int(entryTexts[4]))

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

    doRegionSummary(region, elos)

    return True


def doRegionSummary(region, elos):
    summaryFile = open(
        name = "stats." + region + ".csv",
        mode = "w")

    # calculate how many players in each range of 100 Elo points
    hundredRanges = Counter()

    for elo in elos :
        hundredRanges.update({elo // 100 : 1})

    cumulativePlayers = 0

    summaryFile.write("EloLo,EloHi,NumPlayers,PercentileOf1200+\n")

    for hundred, numPlayers in reversed(sorted(hundredRanges.items())) :
        cumulativePlayers += numPlayers
        summaryFile.write("%d,%d,%d,%.2f\n"
            % (hundred * 100, hundred * 100 + 99, numPlayers,
            100.0 * cumulativePlayers / len(elos)))

    summaryFile.write("total,,%d\n\n" % len(elos))

    topProportionsCumul = [0.1, 0.03, 0.002, ]
    topProportionsOnly = [0.07, 0.028, 0.002, ]
    metals = ["silver", "gold", "platinum", ]

    # Alex Penn likes to assume that 1250+ is still approximately top 25% and
    # calculate other top percentages
    start1250 = bisect.bisect_left(elos, 1250)
    numPlayersTopQuartile = len(elos) - start1250

    summaryFile.write("Metal,EloLo,PlayersIn,PlayersInOrAbove,AssumedPercentile\n")
    summaryFile.write("bronze,1250,%d,%d,25.0%%\n"
        % (round(0.15 / 0.25 * numPlayersTopQuartile), numPlayersTopQuartile))

    for propCumul, propOnly, metal in zip(topProportionsCumul, topProportionsOnly, metals) :
        numOnly = math.floor(propOnly / 0.25 * numPlayersTopQuartile)
        numCumul = math.floor(propCumul / 0.25 * numPlayersTopQuartile)
        eloIdx = -int(numCumul)

        if eloIdx == 0 :
            eloLo = elos[-1] + 1
        else :
            eloLo = elos[eloIdx]

        summaryFile.write("%s,%d,%d,%d,%.1f%%\n"
            % (metal, eloLo, numOnly, numCumul, propCumul * 100))

    summaryFile.close()


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
    #doRegionSummary( "test", [
    #    1250, 1250, 1250, 1300, 1550,
    #    1800, 1850, 1850, 1900, 2150,
    #    ])
    sys.exit(LolScraperMain(sys.argv))


