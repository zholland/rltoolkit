import inspect
import operator
import os.path
from functools import reduce

from .gwGlueEnv import *


# Make sure we can load gridworlds whether we start with demos or gridworld
path = os.path.dirname(inspect.getfile(Gridworld))
gridworldpath = os.path.join(path, "Gridworlds/")

def gwPath():
    return gridworldpath

def gwFilename(name):
    return os.path.join(gridworldpath, name)


### READING and WRITING gridworlds to FILES

def readGridworld(filename):
    "reads a gridworld file into a dictionary list and returns it"
    print(("reading", filename))
    if filename is not None and filename != '':
        input = open(filename, 'r')
        alist = input.readlines()
        uselist = reduce(operator.add, alist)
        list = eval(uselist)
        input.close()
        return list


def getgwinfo(alist):
    """Picks off the basic information from an input dictionary list
       (such as that returned by readGridworld) and returns it"""
    height = alist.get('height')
    width = alist.get('width')
    startsquare = alist.get('startsquare')
    goalsquare = alist.get('goalsquare')
    barrierp = alist.get('barrierp')
    wallp = alist.get('wallp')
    return width, height, startsquare, goalsquare, barrierp, wallp


def prepareWrite(gridworld):
    """makes a dictionary list with the gridworld basics in it, in
       string form for writing. Call this first when writing a gridworld
       out to get the basic information prepared, and then add any extras"""
    gridout = {'height': str(gridworld.height),
               'width': str(gridworld.width),
               'squaresize': str(gridworld.squaresize),
               'barrierp': str(gridworld.barrierp),
               'wallp': str(gridworld.wallp),
               'startsquare': str(gridworld.startsquare),
               'goalsquare': str(gridworld.goalsquare)}
    return gridout


def writeGridworld(dlist, filename):
    "writes a dictionary list to the filename"
    print(("writing to file", filename))
    if filename != None and filename != '':
        output = open(filename, 'w')
        gridout = ["{"]
        # force width, height, squaresize, startsquare and goalsquare to be printed first
        # to make the resulting file more human readable
        gridout.append("'width':" + str(dlist['width']) + ", \n")
        gridout.append("'height':" + str(dlist['height']) + ", \n")
        gridout.append("'squaresize':" + str(dlist['squaresize']) + ", \n")
        gridout.append("'startsquare':" + str(dlist['startsquare']) + ", \n")
        gridout.append("'goalsquare':" + str(dlist['goalsquare']) + ", \n")
        for k, v in list(dlist.items()):
            if not k in ['width', 'height', 'squaresize', 'startsquare',
                         'goalsquare']:
                gridout.append("'" + k + "'" + ':' + v + ", \n")
        gridout.append("'file': '" + str(
            filename) + "'}")  # just so that the last , is ok :)
        output.writelines(gridout)
        output.close()


def convert(filename):
    gwDict = readGridworld(gwFilename(filename))
    # [up, right, down, left] to [up, down, left, right]

    def fixit(lst):
        a, b, c, d = lst
        return [a, c, d, b]
    gwDict['wallp'] = list(map(fixit, gwDict['wallp']))

    for key in gwDict:
        gwDict[key] = str(gwDict[key])

    if 'file' in gwDict:
        gwDict.pop('file')

    head, tail = os.path.split(gwFilename(filename))
    writeGridworld(gwDict, '{}/a{}'.format(head, tail))


if __name__ == '__main__':
    for fname in os.listdir(gridworldpath):
        if 'gw' in fname:
            convert(fname)