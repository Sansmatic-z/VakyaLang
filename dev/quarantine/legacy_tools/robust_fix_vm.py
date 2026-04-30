import re

with open("vm_temp.py", "r") as f:
    content = f.read()

builtins_start = content.find("def _init_builtins(self)")
builtins_end = content.find("def _execute(self)")

if builtins_start != -1 and builtins_end != -1:
    prefix = content[:builtins_start]
    suffix = content[builtins_end:]
    
    new_builtins = """def _init_builtins(self) -> Dict[str, Callable]:
        \"\"\"Initialize builtin functions.\"\"\"
        import os
        import platform
        import math
        import sys
        import time

        # Get the directory of vm.py, then go up 3 levels to find the unified root
        vm_dir = os.path.dirname(os.path.abspath(__file__))
        unified_root = os.path.abspath(os.path.join(vm_dir, '..', '..'))
        if unified_root not in sys.path:
            sys.path.insert(0, unified_root)

        from sansmatic.src.engine import SansmaticEngine, ProofError
        from atmalipi.src.engine import AtmaLipiEngine, AtmaValue
        from runtime.src.errors import VMError

        # Math helper functions
        def _math_cos(x): return math.cos(float(x))
        def _math_sin(x): return math.sin(float(x))
        def _math_tan(x): return math.tan(float(x))
        def _math_sqrt(x): return math.sqrt(float(x))
        def _math_abs(x): return abs(float(x))
        def _math_floor(x): return math.floor(float(x))
        def _math_ceil(x): return math.ceil(float(x))
        def _math_round(x): return round(float(x))
        def _math_degrees(x): return math.degrees(float(x))
        def _math_radians(x): return math.radians(float(x))
        
        _sansmatic = SansmaticEngine(verbose=True)
        _atmalipi = AtmaLipiEngine()

        try:
            bridge_dir = os.path.join(vm_dir, 'bridge')
            if bridge_dir not in sys.path:
                sys.path.append(bridge_dir)
            from chitrakala.pixel_engine import ChitraCanvas, ChitraColor
            from chitrakala.colors import get_color, list_colors
            from chitrakala.png_encoder import save_png, load_png
            from chitrakala.primitives import draw_point, draw_line, draw_circle, draw_rectangle, draw_polygon
            from chitrakala.bitmap_font import draw_text
        except ImportError:
            pass

        def _read_file(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
                
        def _write_file(path, content, mode='w'):
            with open(path, mode, encoding='utf-8') as f:
                f.write(str(content))
            return None

        def _make_dir(path):
            os.makedirs(path, exist_ok=True)
            return None
            
        def _http_get(url, headers_dict=None):
            import urllib.request
            headers = headers_dict if headers_dict else {'User-Agent': 'VakyaLang/3.0'}
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=30) as response:
                    return response.read().decode('utf-8')
            except Exception as e:
                return f"HTTP Error: {e}"

        def _http_post(url, data, headers_dict=None):
            import urllib.request
            headers = headers_dict if headers_dict else {'User-Agent': 'VakyaLang/3.0'}
            try:
                req = urllib.request.Request(url, data=str(data).encode('utf-8'), headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=30) as response:
                    return response.read().decode('utf-8')
            except Exception as e:
                return f"HTTP Error: {e}"

        def _vak_type(obj):
            t = type(obj)
            if t is int: return "संख्या"
            if t is float: return "संख्या"
            if t is str: return "तार"
            if t is bool: return "बूलियन"
            if t is list: return "सूची"
            if t is dict: return "शब्दकोश"
            if obj is None: return "शून्य"
            if isinstance(obj, VakInstance): return obj.klass.name
            return "अज्ञात"

        def _get_time(): return time.time()
        def _sleep(seconds): time.sleep(float(seconds))
        
        def _atma_wrap(val, bhav=None, avastha=None):
            return AtmaValue(val, bhav, avastha)

        def _re_match(pattern, string):
            import re
            return bool(re.match(pattern, string))

        def _re_replace(pattern, repl, string):
            import re
            return re.sub(pattern, repl, string)

        def _json_encode(obj):
            import json
            return json.dumps(obj)

        def _json_decode(string):
            import json
            return json.loads(string)

        def _start_thread(func, *args):
            import threading
            t = threading.Thread(target=func, args=args)
            t.start()
            return t

        # Python Bridge functions
        try:
            sys.path.insert(0, os.path.abspath(os.path.join(vm_dir, '..', 'stdlib')))
            from py_bridge import पायथन_आयात, पायथन_चलाओ, पायथन_मूल्यांकन
        except ImportError:
            def पायथन_आयात(*args): return None
            def पायथन_चलाओ(*args): return None
            def पायथन_मूल्यांकन(*args): return None

        # Chitrakala implementations
        def _chitra_canvas_impl(w, h, c="white"):
            return ChitraCanvas(int(w), int(h), get_color(c) if isinstance(c, str) else c)
        def _chitra_fill_impl(canv, c):
            canv.fill(get_color(c) if isinstance(c, str) else c)
        def _chitra_point_impl(canv, x, y, c):
            draw_point(canv, int(x), int(y), get_color(c) if isinstance(c, str) else c)
        def _chitra_line_impl(canv, x1, y1, x2, y2, c):
            draw_line(canv, int(x1), int(y1), int(x2), int(y2), get_color(c) if isinstance(c, str) else c)
        def _chitra_circle_impl(canv, x, y, r, c, fill=False):
            draw_circle(canv, int(x), int(y), int(r), get_color(c) if isinstance(c, str) else c, bool(fill))
        def _chitra_rect_impl(canv, x, y, w, h, c, fill=False):
            draw_rectangle(canv, int(x), int(y), int(w), int(h), get_color(c) if isinstance(c, str) else c, bool(fill))
        def _chitra_polygon_impl(canv, pts, c, fill=False):
            draw_polygon(canv, [(int(p[0]), int(p[1])) for p in pts], get_color(c) if isinstance(c, str) else c, bool(fill))
        def _chitra_text_impl(canv, x, y, text, font=None, size=1, c="black"):
            draw_text(canv, int(x), int(y), str(text), get_color(c) if isinstance(c, str) else c, None, int(size))
        def _chitra_save_impl(canv, path):
            save_png(canv, str(path))
        def _chitra_load_impl(path):
            return load_png(str(path))
        def _chitra_color_impl(c):
            return get_color(str(c))
        def _chitra_colors_impl():
            return list_colors()
        def _chitra_width_impl(canv):
            return canv.width
        def _chitra_height_impl(canv):
            return canv.height
        def _chitra_pixel_get_impl(canv, x, y):
            return canv.get_pixel(int(x), int(y))
        def _chitra_pixel_set_impl(canv, x, y, c):
            canv.set_pixel(int(x), int(y), get_color(c) if isinstance(c, str) else c)

        return {
            'पाठ_कर': str,
            'str': str,
            'परास': range,
            'range': range,
            'दीर्घता': len,
            'len': len,
            'प्रकार': _vak_type,
            'type': _vak_type,
            'संख्या': int,
            'int': int,
            'दशमलव': float,
            'float': float,
            'मुद्रय': print,
            'print': print,
            'पठन': _read_file,
            'लेखन': _write_file,
            'अस्तित्व': os.path.exists,
            'मिटाओ': lambda p: os.remove(p) if os.path.exists(p) else None,
            'सूची_निर्देशिका': os.listdir,
            'बनाओ_निर्देशिका': _make_dir,
            'परिवेश_प्राप्त': os.getenv,
            'परिवेश_सेट': os.putenv,
            'प्रणाली_कमांड': os.system,
            'मंच': platform.system,
            'कार्य_निर्देशिका': os.getcwd,
            'संयोग': lambda lst, sep="": sep.join(str(x) for x in lst),
            'विभाजन': lambda s, sep=" ": s.split(sep),
            'छाँटो': lambda s: s.strip(),
            'उच्च': lambda s: s.upper() if isinstance(s, str) else s,
            'निम्न': lambda s: s.lower() if isinstance(s, str) else s,
            'पूर्णांक_कर': int,
            'क्रमबद्ध': sorted,
            'योग': sum,
            'अधिकतम': max,
            'न्यूनतम': min,
            'कुंजियाँ': lambda d: list(d.keys()) if isinstance(d, dict) else [],
            'मान': lambda d: list(d.values()) if isinstance(d, dict) else [],
            'वर्गमूल': math.sqrt,
            'जाल_लाओ': _http_get,
            'जाल_भेजो': _http_post,
            'समय': _get_time,
            'निद्रा': _sleep,
            'धागा_शुरू': _start_thread,
            'रेगेक्स_खोज': _re_match,
            'रेगेक्स_बदलो': _re_replace,
            'जेसन_लिखो': _json_encode,
            'जेसन_पढ़ो': _json_decode,
            'पायथन_आयात': पायथन_आयात,
            'पायथन_चलाओ': पायथन_चलाओ,
            'पायथन_मूल्यांकन': पायथन_मूल्यांकन,
            'अक्षर_मान': ord,
            
            # Sansmatic Builtins
            'परिभाषय': lambda *args: _sansmatic.define(str(args[0]), args[1]),
            'दावा': lambda *args: _sansmatic.assert_fact(str(args[0]), str(args[1]), str(args[2]), str(args[3]) if len(args)>3 else None),
            'नियम': lambda *args: _sansmatic.rule((str(args[0]), str(args[1]), str(args[2])), (str(args[3]), str(args[4]), str(args[5]))),
            'मूल्यांकन': lambda *args: _sansmatic.evaluate(str(args[0]), str(args[1]), str(args[2])),
            'सिद्ध_है': lambda *args: _sansmatic.is_provable(str(args[0]), str(args[1]), str(args[2])),
            
            # AtmaLipi Builtins
            'आत्म_मूल्य': _atma_wrap,
            'भाव_पढ़ो': lambda *args: _atmalipi.read_bhav(str(args[0])),
            'अवस्था_पढ़ो': lambda *args: _atmalipi.read_avastha(str(args[0])),
            'सभी_भाव': lambda *args: [f"{k} → {v}" for k, v in _atmalipi.all_bhav().items()],
            'सभी_अवस्था': lambda *args: [f"{k} → {v}" for k, v in _atmalipi.all_avastha().items()],
            'आत्म_इतिहास': lambda *args: _atmalipi.get_history(),
            'आत्म_है': lambda *args: isinstance(args[0], AtmaValue) if args else False,
            'आत्म_भाव': lambda *args: args[0].bhav or "शून्य" if args and isinstance(args[0], AtmaValue) else "शून्य",
            'आत्म_अवस्था': lambda *args: args[0].avastha or "शून्य" if args and isinstance(args[0], AtmaValue) else "शून्य",
            'आत्म_मूल': lambda *args: args[0].value if args and isinstance(args[0], AtmaValue) else (args[0] if args else None),

            # Chitrakala (चित्रकला) - Visual Library Builtins
            # Import Chitrakala modules
            '_chitra_canvas': lambda *args: _chitra_canvas_impl(*args),
            '_chitra_fill': lambda *args: _chitra_fill_impl(*args),
            '_chitra_point': lambda *args: _chitra_point_impl(*args),
            '_chitra_line': lambda *args: _chitra_line_impl(*args),
            '_chitra_circle': lambda *args: _chitra_circle_impl(*args),
            '_chitra_rect': lambda *args: _chitra_rect_impl(*args),
            '_chitra_polygon': lambda *args: _chitra_polygon_impl(*args),
            '_chitra_text': lambda *args: _chitra_text_impl(*args),
            '_chitra_save': lambda *args: _chitra_save_impl(*args),
            '_chitra_load': lambda *args: _chitra_load_impl(*args),
            '_chitra_color': lambda *args: _chitra_color_impl(*args),
            '_chitra_colors': lambda *args: _chitra_colors_impl(*args),
            '_chitra_width': lambda *args: _chitra_width_impl(*args),
            '_chitra_height': lambda *args: _chitra_height_impl(*args),
            '_chitra_pixel_get': lambda *args: _chitra_pixel_get_impl(*args),
            '_chitra_pixel_set': lambda *args: _chitra_pixel_set_impl(*args),
        }\n\n    """
    
    with open("runtime/src/vm.py", "w") as f:
        f.write(prefix + new_builtins + suffix)
    print("Fixed vm.py robustly")
else:
    print(f"Could not find start/end: {builtins_start}, {builtins_end}")
