comments_fragment = '''
fragment Comments on DiscussionNode {
  comments {
    edges {
      node {
        id
        text
        createdAt
        author {
          name
        }
      }
    }
  }
}
'''

file_fragment = '''
fragment FileBasic on FileInterface {
    id
    name
    __typename
    createdAt

    discussion {
      ...Comments
    }

    ... on SimpleFileNode {
        fileName
        accessUrl
    }

    ... on PathologySlideNode {
        isReady
        thumbnailUrl
        dziUrl
        slideProperties {
          mpp
          magnification
        }
        pointClouds {
          edges {
            node {
              id
              statistics {
                color {
                  value
                  name
                }
                value
              }
              points {
                edges {
                  node {
                    x
                    y
                    value
                  }
                }
              }
            }
          }
        }
    }

    ... on DicomStudyFileNode {
        study: dicomStudy {
          accessToken
          dicomwebUrl
          studyInstanceUid
        }
    }

    ... on FormFileNode{
      form{
        id
      }
    }
}
''' + comments_fragment

folder_fragment = '''fragment FileChildren on FileInterface {
  children(
    after: $after,
    first: $page_size,
    name_Istartswith: $search,
    name_Icontains: $prefix_search
  ) {
    edges {
      node {
        ...FileBasic
      }
    }
  }
}  
''' + file_fragment

query_file = '''
query GetFile($id: ID!) {
  file(id: $id) {
        ...FileBasic
    }
}
''' + file_fragment


query_folder = '''
query FileChildren(
  $id: ID!, $after: String, $page_size: Int, 
  $search: String, $prefix_search: String
) {
  file(id: $id) {
    ...FileBasic
    ...FileChildren
  }
}
''' + folder_fragment

query_pathologyslide_download = '''
query GetPathologySlideDownload($id: ID!) {
  file(id: $id) {
    ... on PathologySlideNode {
      downloadUrl
    }
  }
}
'''

query_pathologyslide_masks = '''
query GetPathologySlideMasks($id: ID!) {
  file(id: $id) {
    ... on PathologySlideNode {
      tiledMasks {
      	edges {
          node {
            id
            author {
              name
            }
            algorithmRun {
              discussion {
                ...Comments
              }
              ratings {
                score
                author {
                  name
                }
              }
              algorithm {
                name
              }
            }
            colorMap {
              id
              name
              colors {
                edges {
                  node {
                    name
                    key
                    value
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
''' + comments_fragment

query_pathologyslide_markers = '''
query GetPathologySlideMarkers($id: ID!) {
  file(id: $id) {
    ... on PathologySlideNode {
      markers {
      	edges {
          node {
            id
            x
            y
            rotation
            width
            height
            author {
              name
            }
            number
            discussion {
              ...Comments
            }
          }
        }
      }
    }
  }
}
''' + comments_fragment

query_tiledmask_tiles = '''
query GetTiledMaskTiles($id: ID!) {
  tiledMask(id: $id) {
    tileSize
    tilesUrl
    scale
    tiles {
      x
      y
      level
    }
  }
}
'''
