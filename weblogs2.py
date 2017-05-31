[
["decode"],
["json_load"],

["add_filename", {"column": "filename"}],

#############
# uri and referer parse
#############

["join", {"columns": ["cs-host", "uri"], "output_column": "uri_"}],
["lowercase_value", {"column": "uri_"}],
["url_parse", {"column": "uri_"}],
["flatten_dict", {"columns": ["uri_"]}],
["convert_to_array", {"column": "uri_.path", "separator": "/"}],
["split_array", {"column": "uri_.path", "output_columns": ["uri_.path.0", "uri.path.1", "uri.path.2", "uri.path.3", "uri.path.4", "uri.path.5", "uri.path.6", "uri.path.7", "uri.path.8"] }],
["code_snippet", {"code":'''
line['uri.page'] = next(iter(filter(None, map(line.get, map(lambda n: 'uri.path.' + str(n), range(8, 1, -1))))), None)
'''}],

["lowercase_value", {"column": "referer"}],
["url_parse", {"column": "referer"}],
["flatten_dict", {"columns": ["referer"]}],
["convert_to_array", {"column": "referer.path", "separator": "/"}],
["split_array", {"column": "referer.path", "output_columns": ["referer.path.0", "referer.path.1", "referer.path.2", "referer.path.3", "referer.path.4", "referer.path.5", "referer.path.6", "referer.path.7", "referer.path.8"] }],
["code_snippet", {"code":'''
line['referer.page'] = next(iter(filter(None, map(line.get, map(lambda n: 'uri.path.' + str(n), range(8, 1, -1))))), None)
'''}],

["code_snippet", {"code":'''
import urllib.parse
uri_keep_parameters = {
    # location indicators
    'concept',
    'entity',
    'gadgettype',
    'gadget',
    'gadgetpath',
    'menu',
    'page',
    'path',
    'report',
    'reportname',
    'resolverkey',
    'rdreport',

    # oids
    'oid',
    'oidtoken',
    'id',
    'asset',
    'assetcontext',
    'topic',
    'stream',
    'conversationoid',
    'imageoid',
    'room',
    'selected',
    'contextoid',

    # context
    'primaryscopecontext',
    'roomcontext',

    # report parameters
    'project',
    'program',
    'teamroom',
    'schedule',
    'assettype',
    'aggregationtype',
    'duration',
    'interval',
    'isbycount',
    'period',
    'showweekends',

    # detail widget parameters
    'mode',
    'newtype',

    # misc
    'assetfacet',
    'aspage',
    'norender',
    'feat-nav'
}
referer_keep_parameters = {
    # location indicators
    'concept',
    'entity',
    'gadgettype',
    'gadget',
    'gadgetpath',
    'menu',
    'page',
    'path',
    'report',
    'reportname',
    'resolverkey',
    'rdreport',

    # misc
    'assetfacet',
    'feat-nav'
}

def parse_querystring(qs, keep_parameters):
    output = {}
    if qs and len(qs):
        pairs = [s for s in qs.split('&')]
        for name_value in pairs:
            if not name_value:
                continue
            nv = name_value.split('=', 1)
            if len(nv) != 2:
                nv.append('')
            name = urllib.parse.unquote_plus(nv[0])
            if name in keep_parameters:
                value = urllib.parse.unquote_plus(nv[1])
                if name in output:
                    output[name] = output[name] + ',' + value
                else:
                    output[name] = value
    return output

line['uri.query'] = parse_querystring(line.get('uri_.query'), uri_keep_parameters)
line['referer.query'] = parse_querystring(line.get('referer.query'), referer_keep_parameters)
''', "import_list": ["urllib.parse"]}],
["flatten_dict", {"columns": ["uri.query", "referer.query"]}],

# trim leading slashes
["regex_replace", {"column": "uri.query.gadget", "regex": "^/+", "repl_string": ""}],
["regex_replace", {"column": "uri.query.gadgetpath", "regex": "^/+", "repl_string": ""}],
["regex_replace", {"column": "uri.query.page", "regex": "^/+", "repl_string": ""}],
["regex_replace", {"column": "uri.query.path", "regex": "^/+", "repl_string": ""}],
["regex_replace", {"column": "uri.query.resolverkey", "regex": "^/+", "repl_string": ""}],
["regex_replace", {"column": "referer.query.gadget", "regex": "^/+", "repl_string": ""}],
["regex_replace", {"column": "referer.query.gadgetpath", "regex": "^/+", "repl_string": ""}],
["regex_replace", {"column": "referer.query.page", "regex": "^/+", "repl_string": ""}],
["regex_replace", {"column": "referer.query.path", "regex": "^/+", "repl_string": ""}],
["regex_replace", {"column": "referer.query.resolverkey", "regex": "^/+", "repl_string": ""}],

# capture instance
["code_snippet", {"code":'''
instance = None
path1 = line.get('uri.path.1', '')
path2 = line.get('uri.path.2')
status = int(line['status'])
if (
        path1 != 's' and re.match(r'[a-zA-Z0-9_-]+$', path1) and
        (path2 or status < 400)
   ):
    instance = path1
else:
    path1 = line.get('referer.path.1', '')
    if path1 != 's' and re.match(r'[a-zA-Z0-9_-]+$', path1):
        instance = path1
if instance:
    line['v1.instance'] = instance
''', "import_list": ["re"]}],

# coalesce  oids
["code_snippet", {"code":'''
cols = (
    'uri.query.oid',
    'uri.query.oidtoken',
    'uri.query.id',
    'uri.query.asset',
    'uri.query.assetcontext',
    'uri.query.topic',
    'uri.query.stream',
    'uri.query.conversationoid',
    'uri.query.imageoid',
    'uri.query.room',
    'uri.query.selected',
    'uri.query.contextoid'
)
assettype = None
assetid = None
oid = next(iter(filter(None, map(line.get, cols))), None)
if not oid and line.get('uri.path.2') == 'api' and line.get('uri.path.3') == 'activitystream':
    oid = line.get('uri.path.4')
if oid:
    m = re.match(r'(\w+):(\d+)', oid)
    if m:
        (assettype, assetid) = m.groups()
else:
    path2 = line.get('uri.path.2', '')
    path3 = line.get('uri.path.3', '')
    path4 = line.get('uri.path.4', '')
    if line.get('uri.query.newtype'):
        assettype = line['uri.query.newtype']
    elif re.match(r'rest-1(\.oauth)?\.v1$', path2):
        assettype = path4
        assetid = line.get('uri.path.5')
    elif path2 == 'teamroom.mvc':
        assettype = 'teamroom'
        assetid = path4
    elif re.match(r'attachment(\.oauth)?\.(v1|img)$', path2):
        assettype = 'attachment'
        assetid = path3
    elif re.match(r'image(\.oauth)?\.(v1|img)$', path2):
        assettype = 'image'
        assetid = path3
    elif re.match(r'embedded(\.oauth)?\.(v1|img)$', path2):
        assettype = 'embeddedimage'
        assetid = path3
if assettype:
    line['v1.assettype'] = assettype
if assetid and re.match(r'\d+$', str(assetid)):
    line['v1.assetid'] = assetid
''', "import_list": ["re"]}],

# globally unique asset
["code_snippet", {"code":'''
if line.get('v1.instance') and line.get('v1.assettype') and line.get('v1.assetid'):
    line['v1.asset'] = line['v1.instance'] + '/' + line['v1.assettype'] + ':' + line['v1.assetid']
'''}],
["hash", {"column": "v1.asset"}],

# coalesce  context
["code_snippet", {"code":'''
cols = (
    'uri.query.primaryscopecontext',
    'uri.query.roomcontext'
)
contexttype = None
contextid = None
oid = next(iter(filter(None, map(line.get, cols))), None)
if oid:
    m = re.match(r'(\w+):(\d+)', oid)
    if m:
        (contexttype, contextid) = m.groups()
if contexttype:
    line['v1.contexttype'] = contexttype
if contextid:
    line['v1.contextid'] = contextid
''', "import_list": ["re"]}],

# globally unique context
["code_snippet", {"code":'''
if line.get('v1.instance') and line.get('v1.contexttype') and line.get('v1.contextid'):
    line['v1.context'] = line['v1.instance'] + '/' + line['v1.contexttype'] + ':' + line['v1.contextid']
'''}],
["hash", {"column": "v1.context"}],

# calculate view.1
["code_snippet", {"code":'''
view1 = None
if line.get('uri.path.1') == 's':
    view1 = 's'
else:
    path2 = line.get('uri.path.2', '')
    path3 = line.get('uri.path.3', '')
    path4 = line.get('uri.path.4', '')
    if path2 == 'api':
        if re.match(r'[a-z]\w*$', path4):
            view1 = path3 + '/' + path4
        else:
            view1 = path3
    elif re.search(r'\.mvc$', path2):
        if re.match(r'[a-z]\w*$', path3):
            view1 = path2 + '/' + path3
        else:
            view1 = path2
    elif re.search(r'\.(v1|img|aspx)$', path2):
        view1 = path2
if view1:
    line['v1.view.1'] = view1
''', "import_list": ["re"]}],

# calculate view.2
["code_snippet", {"code":'''
cols = (
    'uri.query.menu',
    'uri.query.page',
    'uri.query.gadgettype',
    'uri.query.gadget',
    'uri.query.gadgetpath',
    'uri.query.entity',
    'uri.query.path',
    'uri.query.concept',
    'uri.query.report',
    'uri.query.reportname',
    'uri.query.resolverkey',
    'uri.query.rdreport'
)
view2 = None
if line.get('uri.path.1') == 's':
    view2 = line.get('uri.path.3')
elif re.match(r'rest-1(\.oauth)?\.v1$', line.get('uri.path.2', '')):
    view2 = line.get('uri.path.3')
else:
    view2 = next(iter(filter(None, map(line.get, cols))), None)
if view2:
    line['v1.view.2'] = re.sub(r'\d+$', '...', view2)
''', "import_list": ["re"]}],

# calculate v1.from
["code_snippet", {"code":'''
from1 = None
if line.get('referer.path.1') == 's':
    from1 = 's'
else:
    path2 = line.get('referer.path.2', '')
    path3 = line.get('referer.path.3', '')
    path4 = line.get('referer.path.4', '')
    if path2 == 'api':
        if re.match(r'[a-z]\w*$', str(path4)):
            from1 = path3 + '/' + path4
        else:
            from1 = path3
    elif re.search(r'\.mvc$', str(path2)):
        if re.match(r'[a-z]\w*$', str(path3)):
            from1 = path2 + '/' + path3
        else:
            from1 = path2
    elif re.search(r'\.(v1|img|aspx)$', str(path2)):
        from1 = path2

cols = (
    'referer.query.menu',
    'referer.query.page',
    'referer.query.gadgettype',
    'referer.query.gadget',
    'referer.query.gadgetpath',
    'referer.query.entity',
    'referer.query.path',
    'referer.query.concept',
    'referer.query.report',
    'referer.query.reportname',
    'referer.query.resolverkey',
    'referer.query.rdreport'
)
from2 = next(iter(filter(None, map(line.get, cols))), None)
if from1 or from2:
    line['v1.from'] = (from1 or '-') + ':' + (from2 or '-')
''', "import_list": ["re"]}],

# target and source
["code_snippet", {"code":'''
targethost = line.get('_uri.hostname')
targettype = None
target = None
sourcehost = line.get('referer.hostname')
sourcetype = None
source = None
v1version = None

nn = lambda value: value and re.sub(r'\d+$', r'#', value)
xx = lambda value: value and re.sub(r'(?<![a-z0-9])([0-9a-f]{2}-?)+$', r'#', value)
ah = lambda value: value and re.sub(r'^(ahreport|ahpreview).*$', r'\1#', value)
s = lambda values: '/'.join(filter(None, values)) or None
f = lambda name: line.get(name)
match = lambda pattern: functools.partial(re.search, pattern)
find = lambda values, predicate: next((i for i, value in enumerate(values) if predicate(value)), None)
first = lambda values: next((value for value in values if value != None), None)

# target parsed from 'uri'
path = list(filter(None, map(f, map(lambda n: 'uri.path.' + str(n), range(1, 9)))))
route = path[1:]
at = first(find(route, match(pattern)) for pattern in (r'\.v1$', r'\.img$'))
if at:
    route = route[at:]

if not path or not re.match(r'[a-z0-9_-]+$', path[0]):
    targettype = 'root'
elif path[0] == 's':
    targettype = 'static'
    v1version = s(path[1:2])
    target = s(path[2:3])
elif not route:
    targettype = 'other'
elif re.match(r'(rest-1|meta|query)(\.oauth|\.legacy)?\.v1', route[0]):
    targettype = 'api'
    target = route[0][:route[0].index('.')]
elif route[0] == 'ui.v1':
    targettype = 'gadget'
    target = f('uri.query.gadgettype') or f('uri.query.gadget') or 'none'
elif route[0] == 'entity.v1':
    targettype = 'entity'
    target = xx(f('uri.query.entity')) or 'none'
elif route[0] == 'export.v1':
    targettype = 'export'
    target = f('uri.query.path')
elif route[0:2] == ['gadgetview.mvc', 'rendergadget']:
    targettype = 'gadget'
    target = f('uri.query.gadgetpath')
elif route[0] == 'analyticsintegration.mvc':
    targettype = 'analytics'
    target = s(route[1:2] + [ah(f('uri.query.rdreport'))])
elif route[0] == 'report.mvc':
    targettype = 'report'
    target = s(route[1:2] + [nn(f('uri.query.report'))])
elif route[0] == 'published.mvc':
    targettype = 'mvc'
    target = xx(s(route[0:2]))
elif re.search(r'\.mvc$', route[0]):
    targettype = 'mvc'
    target = nn(s(route[0:2]))
elif route[0] == 'api' and route[1] and re.match(r'report', route[1]):
    targettype = 'report'
    target = s(route[1:3] + [nn(f('uri.query.report')) or nn(f('uri.query.reportname'))])
elif route[0] == 'api':
    targettype = 'webapi'
    target = s(route[0:2])
elif route[0] == 'default.aspx':
    page = f('uri.query.page')
    menu = f('uri.query.menu')
    targettype = (page and 'popup') or (menu and 'main') or 'home'
    target = page or menu or 'home'
else:
    targettype = 'other'
    target = route[0]

# source parsed from 'referer'
if sourcehost == targethost:
    path = list(filter(None, map(f, map(lambda n: 'referer.path.' + str(n), range(1, 9)))))
    route = path[1:]
    at = first(find(route, match(pattern)) for pattern in (r'\.v1$', r'\.img$'))
    if at:
        route = route[at:]

    if not path or not re.match(r'[a-z0-9_-]+$', path[0]):
        sourcetype = 'root'
    elif path[0] == 's':
        sourcetype = 'static'
        source = s(path[2:3])
    elif not route:
        sourcetype = 'other'
    elif re.match(r'(rest-1|meta|query)(\.oauth|\.legacy)?\.v1', route[0]):
        sourcetype = 'api'
        source = route[0][:route[0].index('.')]
    elif route[0] == 'ui.v1':
        sourcetype = 'gadget'
        source = f('referer.query.gadgettype') or f('referer.query.gadget') or 'none'
    elif route[0] == 'entity.v1':
        sourcetype = 'entity'
        source = xx(f('referer.query.entity')) or 'none'
    elif route[0] == 'export.v1':
        sourcetype = 'export'
        source = f('referer.query.path')
    elif route[0:2] == ['gadgetview.mvc', 'rendergadget']:
        sourcetype = 'gadget'
        source = f('referer.query.gadgetpath')
    elif route[0] == 'analyticsintegration.mvc':
        sourcetype = 'analytics'
        source = s(route[1:2] + [ah(f('referer.query.rdreport'))])
    elif route[0] == 'report.mvc':
        sourcetype = 'report'
        source = s(route[1:2] + [nn(f('referer.query.report'))])
    elif route[0] == 'published.mvc':
        sourcetype = 'mvc'
        source = xx(s(route[0:2]))
    elif re.search(r'\.mvc$', route[0]):
        sourcetype = 'mvc'
        source = nn(s(route[0:2]))
    elif route[0] == 'api' and route[1] and re.match(r'report', route[1]):
        sourcetype = 'report'
        source = s(route[1:3] + [nn(f('referer.query.report')) or nn(f('referer.query.reportname'))])
    elif route[0] == 'api':
        sourcetype = 'webapi'
        source = s(route[0:2])
    elif route[0] == 'default.aspx':
        page = f('referer.query.page')
        menu = f('referer.query.menu')
        sourcetype = (page and 'popup') or (menu and 'main') or 'home'
        source = page or menu or 'home'
    else:
        sourcetype = 'other'
        source = route[0]

if targettype:
    line['v1.target.type'] = targettype
if target:
    line['v1.target'] = target
if sourcetype:
    line['v1.source.type'] = sourcetype
if source:
    line['v1.source'] = source
if v1version:
    line['v1.version'] = v1version
''', "import_list": ["re", "functools"]}],

# dump

["omit", {"columns": ["uri_", "uri_.scheme", "uri_.params", "uri_.hostname", "uri_.port", "uri_.fragment",
    "uri_.path", "uri_.path.0",
    "uri_.query", "uri.query",
    "referer.params", "referer.fragment",
    "referer.path", "referer.path.0",
    "referer.query"]}],

["json_dump"]
]