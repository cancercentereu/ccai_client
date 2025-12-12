comment_fragment = """
fragment Comment on CommentNode {
    id
    text
    createdAt
    author {
        name
    }
}
"""

discussion_fragment = """
fragment Discussion on DiscussionNode {
    id
    comments {
        edges {
            node {
                ...Comment
            }
        }
    }
}
""" + comment_fragment

colormap_fragment = """
fragment ColorMap on ColorMapNode {
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
"""

annotations_fragment = """
fragment Annotations on AnnotationNode {
    id
    number
    author {
        name
    }
    shapeType
    shapeData
    color
    label
    isLabelVisible
    slideId
    pointType
    createdAt
    discussion {
        ...Discussion
    }
}
""" + discussion_fragment

file_fragment = """
fragment FileBasic on FileInterface {
    id
    name
    __typename
    createdAt
    tags {
        id
        value
    }

    discussion {
        ...Discussion
    }

    ... on SimpleFileNode {
        fileName
        accessUrl
    }

    ... on PathologySlideNode {
        isReady
        thumbnailUrl
        processingTask {
            status
            progress
            errorMessage
        }
        
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
                    pointsList
                }
            }
        }
        
    }

    ... on PathologySlideBaseNode {
        isReady
        thumbnailUrl
        processingTask {
            status
            progress
            errorMessage
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

    ... on StudyInterface {
        status {
            name
        }
        assignedTo {
            entity {
                name
            }
        }
    }
}
""" + discussion_fragment

folder_fragment = """
fragment FileChildren on FileInterface {
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
""" + file_fragment

algorithm_run_fragment = """
fragment AlgorithmRun on AlgorithmRunNode {
    id
    algorithm {
        id
        name
    }
    discussion {
        ...Discussion
    }
    ratings {
        score
        author {
            name
        }
    }
}
""" + discussion_fragment

color_map_fragment = """
fragment ColorMap on ColorMapNode {
    id
    name
    codename
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
"""

tiled_mask_fragment = """
fragment TiledMask on TiledMaskNode {
    id
    author {
        name
    }
    colorMap {
        ...ColorMap
    }
    algorithmRun {
        ...AlgorithmRun
    }
    updatedAt
}
""" + color_map_fragment + algorithm_run_fragment

query_file = """
query GetFile($id: ID!) {
    file(id: $id) {
        ...FileBasic
    }
}
""" + file_fragment


query_folder = """
query FileChildren(
    $id: ID!, $after: String, $page_size: Int, 
    $search: String, $prefix_search: String
) {
    file(id: $id) {
        ...FileBasic
        ...FileChildren
    }
}
""" + folder_fragment

query_pathologyslide_download = """
query GetPathologySlideDownload($id: ID!) {
    file(id: $id) {
        ... on PathologySlideNode {
            downloadUrl
        }
    }
}
"""

query_pathologyslide_masks = """
query GetPathologySlideMasks($id: ID!) {
    file(id: $id) {
        ... on PathologySlideNode {
            tiledMasks {
                edges {
                    node {
                        ...TiledMask
                    }
                }
            }
        }
    }
}
""" + tiled_mask_fragment

# deprecated
query_pathologyslide_markers = """
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
                            ...Discussion
                        }
                    }
                }
            }
        }
    }
}
""" + discussion_fragment

query_pathologyslide_annotations = """
query GetPathologySlideAnnotations($id: ID!) {
    file(id: $id) {
        ... on PathologySlideNode {
            annotations {
                edges {
                    node {
                        ...Annotations
                    }
                }
            }
        }
    }
}
""" + annotations_fragment

query_tiledmask_tiles = """
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
"""

query_colormap_by_codename = """
query GetColorMapByCodename($codename: String!) {
    allColorMaps(codename: $codename) {
        edges {
            node {
                ...ColorMap
            }
        }
    }
}
""" + colormap_fragment

mutation_import_annotations_from_geojson = """
mutation ImportAnnotationsFromGeojson($id: ID!, $geojson: String!) {
    importAnnotationsFromGeojson(input: {
        id: $id,
        geojson: $geojson
    }) {
        file {
            id
            name
        }
        annotations {
            ...Annotations
        }
    }
}
""" + annotations_fragment

mutation_update_annotation = """
mutation AnnotationUpdateMutation(
    $id: ID!,
    $shapeData: [Int!],
    $color: ID,
    $label: String,
    $pointType: PointType,
    $isLabelVisible: Boolean
) {
    annotationUpdate(input: {
        id: $id,
        shapeData: $shapeData,
        color: $color,
        label: $label,
        pointType: $pointType,
        isLabelVisible: $isLabelVisible
    }) {
        annotation {
            ...Annotations
        }
    }
}
""" + annotations_fragment

query_entity = """
query GetCurrentEntity {
    entity {
        id
        name
        organization {
            name
        }
    }
}
"""

query_all_algorithms = """
query GetAllAlgorithms{
    allAlgorithms {
        edges {
            node {
                id
                name
            }
        }
    }
}
"""

query_all_color_maps = """
query GetAllColorMaps {
    allColorMaps {
        edges {
            node {
                ...ColorMap
            }
        }
    }
}
""" + color_map_fragment

query_root_file = """
query GetRootFile {
    entity {
        fileRoot {
            ...FileBasic
        }
    }
}
""" + file_fragment

query_deep_search_files = """
query SearchFiles(
    $root_file_id: ID!,
    $deep: Boolean = false,
    $include_root: Boolean = false,
    $search: String = "",
    $search_prefix: String = "",
    $offset: Int = 0,
    $limit: Int = 100,
    $type: String
    $tagsValue: String
) {
    searchFiles(
        rootFileId: $root_file_id,
        deep: $deep,
        includeRoot: $include_root,
        name_Icontains: $search,
        name_Istartswith: $search_prefix,
        offset: $offset,
        first: $limit,
        type: $type
        tagsValue: $tagsValue
    ) {
        edges {
            node {
                ...FileBasic
            }
        }
    }
}
""" + file_fragment

mutation_rename_file = """
mutation RenameFile($id: ID!, $name: String!) {
    fileUpdate(input: {
        id: $id,
        name: $name
    }) {
        file {
            ...FileBasic
        }
    }
}
""" + file_fragment

mutation_delete_file = """
mutation DeleteFile($id: ID!, $parent: ID!) {
    fileDelete(input: {
        id: $id,
        parent: $parent
    }) {
        file {
            ...FileBasic
        }
    }
}
""" + file_fragment

mutation_delete_full_file = """
mutation DeleteFullFile($id: ID!) {
    fileDeleteFull(input: {
        id: $id
    }) {
        file {
            ...FileBasic
        }
    }
}
""" + file_fragment

mutation_link_file = """
mutation LinkFile($id: ID!, $target: ID!) {
    fileLink(input: {
        id: $id,
        target: $target
    }) {
        file {
            ...FileBasic
        }
    }
}
""" + file_fragment

mutation_move_file = """
mutation MoveFile($id: ID!, $parent: ID!, $target:  ID!) {
    fileMove(input: {
        id: $id,
        parent: $parent,
        target: $target
    }) {
        file {
            ...FileBasic
        }
    }
}
""" + file_fragment

mutation_add_subfolder = """
mutation AddSubfolder($parent: ID!, $name: String!) {
    folderCreate(input: {
        parent: $parent,
        name: $name
    }) {
        file {
            ...FileBasic
        }
    }
}
""" + file_fragment

mutation_create_study = """
mutation CreateStudy($parent: ID!, $name: String, $status: ID, $mode: ID, $deadline: DateTime) {
    studyCreate(input: {
        parent: $parent,
        name: $name,
        status: $status,
        mode: $mode,
        deadline: $deadline
    }) {
        file {
            ...FileBasic
        }
    }
}
""" + file_fragment

mutation_run_algorithm = """
mutation RunAlgorithm($slide: ID!, $algorithm: ID!, $roi: ID) {
    algorithmRun(input: {
        slide: $slide,
        algorithm: $algorithm,
        roi: $roi
    }) {
        algorithmRun {
            ...AlgorithmRun
        }
    }
}
""" + algorithm_run_fragment

mutation_upload_container = """
mutation UploadContainer($files: [String!]!) {
    uploadContainerCreate(input: { files: $files }) {
        container {
            id
        }
        presignUpload {
            files {
                url
                method
                data
                headers
            }
        }
    }
}
"""

mutation_pathology_slide_create = """
mutation PathologySlideCreate($container: ID!, $parent: ID!, $name: String!,
 $isCollage: Boolean = false, $anonymize: Boolean = false, $filters: [String!] = []) {
    pathologySlideCreate(input: {
        container: $container,
        parent: $parent,
        name: $name,
        isCollage: $isCollage,
        anonymize: $anonymize,
        filters: $filters
    }) {
        file {
            id
            name
        }
    }
}
"""

mutation_comment_create = """
mutation CommentCreate($discussion: ID!, $text: String!) {
    commentCreate(input: {
        discussion: $discussion,
        text: $text
    }) {
        comment {
            ...Comment
        }
    }
}
""" + comment_fragment

mutation_tiledmask_create = """
mutation TiledMaskCreate(
    $slide: ID!,
    $colorMapId: ID,
    $colorMapCodename: String,
    $uploadsContainer: ID,
    $tileSize: Int,
    $scale: Float,
    $maskType: UploadedMaskType
) {
    tiledMaskCreate(input: {
        slide: $slide,
        colorMapId: $colorMapId,
        colorMapCodename: $colorMapCodename,
        uploadsContainer: $uploadsContainer,
        tileSize: $tileSize,
        scale: $scale,
        maskType: $maskType
    }) {
        tiledMask {
            ...TiledMask
        }
    }
}
""" + tiled_mask_fragment