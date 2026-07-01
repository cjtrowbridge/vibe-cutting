use <../assets/fonts/liberation-sans/LiberationSans-Bold.ttf>
use <../assets/fonts/liberation-sans/LiberationSans-Regular.ttf>

text_value = is_undef(text_value) ? "TEXT" : text_value;
font_name = is_undef(font_name) ? "Liberation Sans:style=Bold" : font_name;
font_size = is_undef(font_size) ? 100 : font_size;
curve_segments = is_undef(curve_segments) ? 48 : curve_segments;

text(
    text = text_value,
    size = font_size,
    font = font_name,
    halign = "center",
    valign = "center",
    direction = "ltr",
    language = "en",
    script = "latin",
    $fn = curve_segments
);
