import json
import os
import re
import string
import sys
from typing import Any

try:
    from py_common import graphql
    from py_common import log
except ModuleNotFoundError:
    print("You need to download the folder 'py_common' from the community repo! (CommunityScrapers/tree/master/scrapers/py_common)",
          file=sys.stderr,
          flush=True)
    sys.exit(0)

SlrPatterns = [
    r'SLR_{Studio}_{Title}_{Resolution}_{SceneId}_{VRType}_{Angle}.{ext}',
    r'SLR_{Studio}_{Title}_original_{SceneId}_{VRType}_{Angle}.{ext}',
    # r'SLR_{Studio}_{Title}_{Resolution}_{SceneId}_{VRType}_{Angle}.{ext}',
    # r'SLR_{Studio}_{Title}_{Resolution}_{SceneId}_{VRType}_{Angle}.{ext}',
]



# Allows us to simply debug the script via CLI args
if len(sys.argv) > 2 and '-d' in sys.argv:
    stdin = sys.argv[sys.argv.index('-d') + 1]
else:
    stdin = sys.stdin.read()

for arg in sys.argv:
    log.debug("Arg: " + arg)

frag = json.loads(stdin)

log.debug(json.dumps(frag))


def getPrimaryFilePath(js):
    scene_id = js['id']
    scene_title = js['title']
    response = graphql.callGraphQL("""
    query GetScenePathBySceneId($id: ID){
      findScene(id: $id){
        path
      }
    }""", {"id": scene_id})

    return response["findScene"]["path"]

# SLR_{Studio}_{Title}_{Resolution}_{SceneId}_{VRType}_{Angle}.{ext}


def parseSlrFileName(path:str) -> dict[str, Any] | None:
    fileName = os.path.basename(path)

    log.debug(fileName)

    SlrPattern = r'^SLR_(?P<Studio>.+?)_'
    SlrPattern += r'(?P<Title>.+?)_'
    SlrPattern += r'((?P<Resolution>\d+[p|P])|original|interpolated)_'
    SlrPattern += r'(?P<SceneId>\d+)_'
    SlrPattern += r'(((?P<VRType>.+)_(?P<Angle>\d+))|(?P<VRType2>.+?))\.'
    SlrPattern += r'(?P<ext>.+)$'

    log.debug(SlrPattern)

    SlrRegex = re.compile(SlrPattern)

    log.debug(SlrRegex)

    match = SlrRegex.match(fileName)

    if (match is None):
        return None

    return {
        'SceneId':  match['SceneId'],
        # 'studio': match['Studio'],
        'title': match['Title'],
        # 'Resolution': match['Resolution'],
        # 'SceneId': match['SceneId'],
        # 'VRType': match['VRType'],
        # 'Angle': match['Angle'],
        # 'ext': match['ext']
    }

try:
    log.debug(json.dumps(getPrimaryFilePath(frag)))

    sceneDataFromFile = parseSlrFileName(getPrimaryFilePath(frag))

    if sceneDataFromFile is None:
        print(json.dumps(None))
        sys.exit(0)

    log.debug(json.dumps(sceneDataFromFile))


    def call_graphql(query, variables=None) -> dict[str,Any] | None:
        return graphql.callGraphQL(query, variables)


    def scrape_scene(url):
        query = """
    query scrapeSceneURL($url: String!) {
        scrapeSceneURL(url: $url) {
            title
            details
            date
            image
            studio {
                name
            }
            tags {
                name
            }
            performers {
                name
            }
            url
        }
    }
    """

        variables = {'url': url}
        log.debug(f'Calling qraphql {variables}')
        qlResult = call_graphql(query, variables)
        log.debug('Done calling qraphql')
        log.debug(f"result {qlResult}")
        return qlResult["scrapeSceneURL"] if qlResult is not None else None

    url = 'https://www.sexlikereal.com/' + sceneDataFromFile['SceneId'] # scenes/ + sceneDataFromFile['title'].replace(' ', '-') + '-'
    log.debug(json.dumps(url))

    if url:
        scrapped = scrape_scene(url)
        log.debug(scrapped)
        print(json.dumps(scrapped).encode().decode('utf-8'))

    else:
        print(json.dumps(None))

except Exception as e:
    log.error(e)