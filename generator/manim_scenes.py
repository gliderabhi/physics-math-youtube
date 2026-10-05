import json
import math
import os
import textwrap

import numpy as np
from manim import (
    Arc,
    BLUE,
    BLUE_D,
    DOWN,
    GRAY,
    GREEN,
    LEFT,
    ORANGE,
    RED,
    RIGHT,
    UL,
    WHITE,
    YELLOW,
    UP,
    Arrow,
    Axes,
    Circle,
    Create,
    DashedLine,
    Dot,
    FadeIn,
    FadeOut,
    GrowArrow,
    Line,
    MathTex,
    MoveAlongPath,
    PURPLE,
    Polygon,
    Scene,
    Square,
    TAU,
    Text,
    UpdateFromAlphaFunc,
    VGroup,
    VMobject,
    Write,
)

COLOR_MAP = {"BLUE": BLUE, "YELLOW": YELLOW, "GREEN": GREEN, "ORANGE": ORANGE, "WHITE": WHITE, "RED": RED}

ORBIT_CENTER = LEFT * 3.5 + UP * 0.2
ORBIT_SCALE = 0.85
ORBIT_PLANET_RADIUS = 1.15
GM = 1.0

LEGEND_POS = RIGHT * 3.3 + UP * 2.7

ENERGY_CENTER = RIGHT * 3.3 + DOWN * 0.3
ENERGY_X_LEN = 5.8
ENERGY_Y_LEN = 3.9
ENERGY_Y_RANGE = (-1.1, 1.3)

FORMULA_POS = DOWN * 3.3

KE_COLOR = WHITE
PE_COLOR = PURPLE


def _color(name: str | None, default=BLUE):
    return COLOR_MAP.get((name or "").upper(), default)


def _wrapped_text(body: str, font_size: int, width_chars: int = 34, color=WHITE) -> Text:
    wrapped = textwrap.fill(body, width=width_chars)
    return Text(wrapped, font_size=font_size, color=color, line_spacing=1.2)


def _safe_mathtex(latex: str, color=YELLOW, font_size: int = 40):
    try:
        return MathTex(latex, color=color, font_size=font_size)
    except Exception:
        return Text(latex, font_size=32, color=color)


def _text_panel(segment: dict, font_size: int) -> VGroup:
    parts = []
    if segment.get("label"):
        parts.append(Text(segment["label"], font_size=28, color=BLUE_D))
    parts.append(_wrapped_text(segment["display_text"], font_size))
    if segment.get("latex"):
        parts.append(_safe_mathtex(segment["latex"]))
    return VGroup(*parts).arrange(DOWN, buff=0.35)


def _check_no_overlap(diagram, text_panel, where: str) -> None:
    """Rectangle-intersection check between the left-side diagram and the right-side
    text panel. Printed loudly (not silently swallowed) so a bad layout shows up in
    the build log instead of only being caught by someone watching the rendered
    video — per the standing rule: verify programmatically, not by sampling frames."""
    d_left, d_right = diagram.get_left()[0], diagram.get_right()[0]
    d_bottom, d_top = diagram.get_bottom()[1], diagram.get_top()[1]
    t_left, t_right = text_panel.get_left()[0], text_panel.get_right()[0]
    t_bottom, t_top = text_panel.get_bottom()[1], text_panel.get_top()[1]

    x_overlap = d_right > t_left and t_right > d_left
    y_overlap = d_top > t_bottom and t_top > d_bottom
    if x_overlap and y_overlap:
        print(
            f"OVERLAP WARNING [{where}]: diagram x=({d_left:.2f},{d_right:.2f}) y=({d_bottom:.2f},{d_top:.2f}) "
            f"overlaps text x=({t_left:.2f},{t_right:.2f}) y=({t_bottom:.2f},{t_top:.2f})"
        )


def _build_vector_path(visual: dict):
    """Axes + a sequence of displacement vectors, optionally with a dashed resultant vector."""
    vectors = visual["vectors"]
    xs, ys = [0.0], [0.0]
    for v in vectors:
        xs.append(xs[-1] + v["dx"])
        ys.append(ys[-1] + v["dy"])

    pad = 1.5
    axes = Axes(
        x_range=[min(0, *xs) - pad, max(0, *xs) + pad, 1],
        y_range=[min(0, *ys) - pad, max(0, *ys) + pad, 1],
        x_length=5.6,
        y_length=4.6,
        axis_config={"include_tip": True, "font_size": 16, "stroke_color": GRAY},
    )

    arrows = VGroup()
    labels = VGroup()
    cx, cy = 0.0, 0.0
    for v in vectors:
        nx, ny = cx + v["dx"], cy + v["dy"]
        start = axes.coords_to_point(cx, cy)
        end = axes.coords_to_point(nx, ny)
        color = _color(v.get("color"), BLUE)
        arrow = Arrow(start, end, buff=0, color=color, stroke_width=6)
        mid = (start + end) / 2
        offset = RIGHT * 0.5 if abs(v["dy"]) > abs(v["dx"]) else DOWN * 0.4
        label = Text(v.get("label", ""), font_size=22, color=color).move_to(mid + offset)
        arrows.add(arrow)
        labels.add(label)
        cx, cy = nx, ny

    group = VGroup(axes, arrows, labels)

    resultant_line, resultant_label = None, None
    if visual.get("show_resultant"):
        start = axes.coords_to_point(0, 0)
        end = axes.coords_to_point(cx, cy)
        resultant_line = DashedLine(start, end, color=YELLOW, stroke_width=6, dash_length=0.12)
        resultant_label = Text(visual.get("resultant_label", "Resultant"), font_size=22, color=YELLOW)
        resultant_label.next_to(resultant_line.get_center(), UP, buff=0.25)
        group.add(resultant_line, resultant_label)

    group.scale(0.95).to_edge(LEFT, buff=0.4)
    return group, axes, arrows, labels, resultant_line, resultant_label


def _build_circular_path(visual: dict):
    """A circular/arc path (for circular-motion distance-vs-displacement problems etc.),
    traced from start_angle_deg through fraction*360 degrees, optionally with a dashed
    chord showing the resultant displacement."""
    radius = visual.get("radius", 2.0)
    fraction = visual.get("fraction", 1.0)
    start_angle = math.radians(visual.get("start_angle_deg", 90))
    color = _color(visual.get("color"), BLUE)
    scale = min(1.0, 2.2 / radius)

    center_point = LEFT * 3.3
    center_dot = Dot(center_point, radius=0.05, color=GRAY)
    arc = Arc(radius=radius * scale, start_angle=start_angle, angle=fraction * TAU, color=color, stroke_width=6)
    arc.move_arc_center_to(center_point)
    start_point = arc.point_from_proportion(0)
    end_point = arc.point_from_proportion(1)
    moving_dot = Dot(start_point, radius=0.08, color=color)

    group = VGroup(center_dot, arc, moving_dot)

    chord, chord_label = None, None
    if visual.get("show_resultant") and fraction < 1.0:
        chord = DashedLine(start_point, end_point, color=YELLOW, stroke_width=6, dash_length=0.12)
        chord_label = Text(visual.get("resultant_label", "Displacement"), font_size=22, color=YELLOW)
        # Push the label away from whichever side the arc bulges toward, not a fixed
        # direction, since that depends on start_angle/fraction.
        arc_mid = arc.point_from_proportion(0.5)
        away = chord.get_center() - arc_mid
        away = away / np.linalg.norm(away) if np.linalg.norm(away) > 1e-6 else UP
        chord_label.move_to(chord.get_center() + away * 0.5)
        group.add(chord, chord_label)
    elif visual.get("show_resultant") and fraction >= 1.0:
        chord_label = Text(visual.get("resultant_label", "Displacement = 0"), font_size=22, color=YELLOW)
        chord_label.next_to(center_point, DOWN, buff=radius * scale + 0.4)
        group.add(chord_label)

    return group, arc, moving_dot, chord, chord_label


def _build_function_graph(visual: dict):
    """A generic labeled x-y line graph (e.g. velocity-time, position-time), one or more
    curves, each optionally shaded underneath (area = displacement on a v-t graph) and
    optionally labeled. Reusable for acceleration, equations of motion, and any
    quantity-vs-time topic."""
    x_range = visual.get("x_range", [0, 10, 2])
    y_range = visual.get("y_range", [0, 10, 2])
    axes = Axes(
        x_range=x_range, y_range=y_range,
        x_length=6.2, y_length=4.2,
        axis_config={"include_tip": True, "stroke_color": GRAY, "font_size": 16},
        x_axis_config={"numbers_to_include": np.arange(x_range[0], x_range[1] + 1e-6, x_range[2])},
        y_axis_config={"numbers_to_include": np.arange(y_range[0], y_range[1] + 1e-6, y_range[2])},
    )
    x_label = Text(visual.get("x_label", "x"), font_size=18, color=GRAY).next_to(axes.x_axis, DOWN, buff=0.2).to_edge(RIGHT, buff=0.1).shift(LEFT * 2)
    y_label = Text(visual.get("y_label", "y"), font_size=18, color=GRAY).next_to(axes.y_axis, UP, buff=0.15).align_to(axes, LEFT)

    base = VGroup(axes, x_label, y_label)
    curve_entries = []  # (curve_mobj, shade_mobj_or_None, label_mobj_or_None, tangent_mobj_or_None)
    for spec in visual.get("curves", []):
        pts = [axes.coords_to_point(x, y) for x, y in spec["points"]]
        color = _color(spec.get("color"), BLUE)
        curve = VMobject(color=color, stroke_width=5)
        curve.set_points_as_corners(pts)

        shade = None
        if spec.get("shade_under"):
            zero_pts = [axes.coords_to_point(x, 0) for x, _ in spec["points"]]
            shade = Polygon(*(pts + list(reversed(zero_pts))), color=color, fill_color=color, fill_opacity=0.22, stroke_width=0)

        label = None
        if spec.get("label"):
            label = Text(spec["label"], font_size=20, color=color).next_to(pts[-1], RIGHT, buff=0.12)

        tangent = None
        if spec.get("tangent_at") is not None:
            tangent = _build_tangent(axes, spec["points"], spec["tangent_at"], color, spec.get("tangent_label"))

        curve_entries.append((curve, shade, label, tangent))

    group = VGroup(
        base,
        *[c for c, _, _, _ in curve_entries],
        *[s for _, s, _, _ in curve_entries if s],
        *[l for _, _, l, _ in curve_entries if l],
        *[t for _, _, _, t in curve_entries if t],
    )
    group.scale(0.95).to_edge(LEFT, buff=0.4)
    return group, base, curve_entries


def _interp_slope_and_point(points: list, x_value: float):
    """Linear-interpolates the curve's (x, y) value and local slope at x_value from its
    point list — this is what lets the tangent actually be drawn at the right place and
    angle instead of narration alone claiming "steeper = faster"."""
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        lo, hi = (x1, x2) if x1 <= x2 else (x2, x1)
        if lo <= x_value <= hi and x2 != x1:
            t = (x_value - x1) / (x2 - x1)
            return x_value, y1 + t * (y2 - y1), (y2 - y1) / (x2 - x1)
    (x1, y1), (x2, y2) = points[0], points[1]
    return points[0][0], points[0][1], ((y2 - y1) / (x2 - x1) if x2 != x1 else 0.0)


def _build_tangent(axes, points: list, x_value: float, color, label: str | None, run: float = 1.3):
    """A short line through the curve at x_value with its real local slope there, plus a
    dashed rise/run right-angle so "slope = rate of change" is something drawn, not just
    spoken. Reused for position-time -> velocity and velocity-time -> acceleration."""
    x0, y0, slope = _interp_slope_and_point(points, x_value)
    p = axes.coords_to_point(x0, y0)
    dx_screen = axes.coords_to_point(x0 + 1, y0)[0] - p[0]
    dy_screen = axes.coords_to_point(x0, y0 + 1)[1] - p[1]
    direction = np.array([dx_screen, dy_screen * slope, 0.0])
    norm = np.linalg.norm(direction)
    direction = direction / norm if norm > 1e-9 else np.array([1.0, 0.0, 0.0])

    tangent_line = Line(p - direction * run, p + direction * run, color=color, stroke_width=5)

    corner = p + RIGHT * run * 0.8
    on_line = p + direction * (run * 0.8 / direction[0]) if abs(direction[0]) > 1e-6 else p + UP * run * 0.8
    run_leg = DashedLine(p, corner, color=GRAY, stroke_width=3, dash_length=0.08)
    rise_leg = DashedLine(corner, on_line, color=GRAY, stroke_width=3, dash_length=0.08)

    group = VGroup(run_leg, rise_leg, tangent_line, Dot(p, radius=0.06, color=color))
    if label:
        group.add(Text(label, font_size=20, color=color).next_to(tangent_line.get_end(), UP, buff=0.08))
    return group


FBD_CENTER = LEFT * 3.3


def _label_direction(arrows: list[dict]):
    """Picks the first cardinal direction (DOWN > UP > LEFT > RIGHT) not already claimed by
    one of this object's own arrows, so the object's name label never lands on top of an
    arrow's label — most commonly, a downward 'Weight' arrow vs. the object's own name."""
    occupied = {"DOWN": False, "UP": False, "LEFT": False, "RIGHT": False}
    for a in arrows:
        dx, dy = a["dx"], a["dy"]
        if abs(dy) >= abs(dx):
            occupied["DOWN" if dy < 0 else "UP"] = True
        else:
            occupied["LEFT" if dx < 0 else "RIGHT"] = True
    for name, vec in (("DOWN", DOWN), ("UP", UP), ("LEFT", LEFT), ("RIGHT", RIGHT)):
        if not occupied[name]:
            return vec
    return DOWN


GROUND_Y = FBD_CENTER[1] - 1.6


def _build_ground(width: float = 7.4):
    """A horizontal surface with hatching. Friction has no meaning without a surface for
    the object to rest on — a friction arrow floating next to a block with nothing drawn
    under it is the text-with-slides failure mode in diagram form; this fixes that."""
    y = GROUND_Y
    left_x, right_x = FBD_CENTER[0] - width / 2, FBD_CENTER[0] + width / 2
    line = Line([left_x, y, 0], [right_x, y, 0], color=GRAY, stroke_width=4)
    ticks = VGroup()
    x = left_x
    while x <= right_x + 1e-6:
        ticks.add(Line([x, y, 0], [x - 0.18, y - 0.22, 0], color=GRAY, stroke_width=2))
        x += 0.35
    return VGroup(line, ticks)


def _build_fbd_object(kind: str, color):
    """The drawn shape for one object kind — every concept word in the narration
    (friction/tension/pulley/lift/observer) needs a real drawn object, not just an
    arrow with a label, so this is where that shape actually gets built."""
    if kind == "pulley":
        wheel = Circle(radius=0.35, color=GRAY, fill_color=GRAY, fill_opacity=0.3, stroke_width=4)
        axle = Dot(wheel.get_center(), radius=0.04, color=GRAY)
        mount = Line(UP * 0.1, UP * 0.5, color=GRAY, stroke_width=4).next_to(wheel, UP, buff=0)
        return VGroup(mount, wheel, axle)
    if kind == "lift":
        cabin = Square(side_length=1.3, color=color, fill_color=color, fill_opacity=0.35, stroke_width=4)
        cable = Line(cabin.get_top(), cabin.get_top() + UP * 1.4, color=GRAY, stroke_width=3)
        return VGroup(cable, cabin)
    if kind == "observer":
        head = Circle(radius=0.14, color=color, fill_color=color, fill_opacity=1).shift(UP * 0.55)
        body = Line(UP * 0.4, DOWN * 0.15, color=color, stroke_width=5)
        legs = VGroup(
            Line(DOWN * 0.15, DOWN * 0.5 + LEFT * 0.2, color=color, stroke_width=5),
            Line(DOWN * 0.15, DOWN * 0.5 + RIGHT * 0.2, color=color, stroke_width=5),
        )
        arms = VGroup(
            Line(UP * 0.25, UP * 0.05 + LEFT * 0.3, color=color, stroke_width=5),
            Line(UP * 0.25, UP * 0.05 + RIGHT * 0.3, color=color, stroke_width=5),
        )
        return VGroup(head, body, legs, arms)
    return Square(side_length=0.7, color=color, fill_color=color, fill_opacity=0.5)  # "block" (default)


def _build_free_body_diagram(visual: dict):
    """One or more objects — blocks, a pulley, a lift cabin, an observer figure — each
    optionally with labeled force/velocity arrows, optionally resting on a drawn ground.
    Reusable for Newton's laws, friction, tension/pulleys, lift problems, equilibrium,
    momentum/collision diagrams — anywhere arrows act ON a drawn object, as opposed to
    vector_path's chained displacement path."""
    group = VGroup()
    if visual.get("ground"):
        group.add(_build_ground())
    if visual.get("rope"):
        # The physical string/rope itself — a pulley or tension arrows with nothing
        # visibly connecting the objects reads as disconnected shapes, not a system.
        # Drawn before the objects so blocks/pulley sit visually on top of its ends.
        rope_pts = [FBD_CENTER + np.array([p[0], p[1], 0.0]) for p in visual["rope"]]
        rope = VMobject(color=GRAY, stroke_width=3)
        rope.set_points_as_corners(rope_pts)
        group.add(rope)

    for obj in visual.get("objects", []):
        pos = FBD_CENTER + np.array([obj["pos"][0], obj["pos"][1], 0.0])
        color = _color(obj.get("color"), BLUE)
        shape = _build_fbd_object(obj.get("kind", "block"), color)
        shape.move_to(pos)
        group.add(shape)
        # Arrows should start at the object's actual edge, not its center — a bare 0.35
        # buff (right for the default 0.7 block) would start an arrow inside a bigger
        # shape like the lift cabin, so size it to whatever was actually drawn.
        arrow_buff = max(shape.width, shape.height) / 2 + 0.05
        if obj.get("label"):
            label_dir = _label_direction(obj.get("arrows", []))
            label = Text(obj["label"], font_size=18, color=WHITE).next_to(shape, label_dir, buff=0.15)
            group.add(label)
        for arrow_spec in obj.get("arrows", []):
            acolor = _color(arrow_spec.get("color"), YELLOW)
            delta = np.array([arrow_spec["dx"], arrow_spec["dy"], 0.0])
            if arrow_spec.get("at_surface"):
                # Friction (and any other force that acts where the object touches the
                # ground, not through its body) anchors at the bottom edge, not the
                # center — a friction arrow drawn through the box's middle looks like
                # it's acting on the body instead of at the contact surface.
                anchor = np.array([pos[0], pos[1] - shape.height / 2, 0.0])
                this_buff = 0.05
            else:
                anchor = pos
                this_buff = arrow_buff
            start = anchor
            end = anchor + delta
            arrow = Arrow(start, end, buff=this_buff, color=acolor, stroke_width=6)
            group.add(arrow)
            if arrow_spec.get("label"):
                dx, dy = arrow_spec["dx"], arrow_spec["dy"]
                if arrow_spec.get("at_surface"):
                    # A below-the-arrow label would land in/under the ground hatching —
                    # always put it above regardless of which way the arrow points.
                    offset = UP * 0.3
                elif abs(dy) <= abs(dx):
                    # Two objects can have arrows pointing AT each other (action-reaction pairs)
                    # that meet at the same midpoint — sign-based offset keeps a leftward- and a
                    # rightward-pointing arrow's labels on opposite sides instead of colliding.
                    offset = (UP if dx >= 0 else DOWN) * 0.3
                else:
                    offset = RIGHT * 0.4
                albl = Text(arrow_spec["label"], font_size=18, color=acolor).move_to(end + offset)
                group.add(albl)
    return group


def _build_reference_frames(visual: dict):
    """A small axis marker per observer/reference frame, each optionally with its own
    velocity arrow. For inertial-vs-non-inertial-frame problems — "from an inertial
    frame..." needs two visibly distinct frames on screen, not just narration."""
    group = VGroup()
    default_positions = [[-5.0, 0.6], [-1.6, 0.6]]
    for i, frame in enumerate(visual.get("frames", [])):
        x, y = frame.get("pos", default_positions[i % len(default_positions)])
        origin = np.array([x, y, 0.0])
        color = _color(frame.get("color"), WHITE)
        x_axis = Arrow(origin, origin + RIGHT * 0.9, buff=0, color=color, stroke_width=4)
        y_axis = Arrow(origin, origin + UP * 0.9, buff=0, color=color, stroke_width=4)
        frame_group = VGroup(x_axis, y_axis, Dot(origin, radius=0.05, color=color))
        if frame.get("label"):
            frame_group.add(Text(frame["label"], font_size=20, color=color).next_to(origin, DOWN, buff=0.25))
        if frame.get("moving"):
            v_arrow = Arrow(origin + DOWN * 0.15, origin + DOWN * 0.15 + RIGHT * 1.3, buff=0, color=YELLOW, stroke_width=5)
            frame_group.add(v_arrow, Text(frame.get("velocity_label", "v"), font_size=20, color=YELLOW).next_to(v_arrow, DOWN, buff=0.1))
        group.add(frame_group)
    group.scale(0.95).to_edge(LEFT, buff=0.6)
    return group


def _simulate_launch(angle_deg: float, speed_factor: float, R: float = ORBIT_PLANET_RADIUS,
                      gm: float = GM, max_r_factor: float = 3.2, dt: float = 0.015, max_steps: int = 4000):
    """Numerically integrates motion under inverse-square gravity for an object launched
    from the top of the planet. speed_factor is relative to escape velocity at the surface.
    Returns (points, speeds, outcome); points[i]/speeds[i] let callers derive KE, PE and
    total energy at every sampled instant, so conservation of energy can be plotted directly."""
    angle = math.radians(angle_deg)
    v_escape = math.sqrt(2 * gm / R)
    speed = speed_factor * v_escape
    x, y = 0.0, R
    vx, vy = speed * math.sin(angle), speed * math.cos(angle)
    points = [(x, y)]
    speeds = [speed]
    outcome = "returned"
    max_r = R * max_r_factor
    for i in range(max_steps):
        r = math.hypot(x, y)
        if r > max_r:
            outcome = "escaped"
            break
        ax, ay = -gm * x / r**3, -gm * y / r**3
        vx += ax * dt
        vy += ay * dt
        x += vx * dt
        y += vy * dt
        points.append((x, y))
        speeds.append(math.hypot(vx, vy))
        if i > 5 and math.hypot(x, y) < R * 0.98:
            outcome = "returned"
            break
    if len(points) > 150:
        step = len(points) // 150
        points = points[::step] + [points[-1]]
        speeds = speeds[::step] + [speeds[-1]]
    return points, speeds, outcome


def _sim_to_scene(x: float, y: float):
    return ORBIT_CENTER + np.array([x * ORBIT_SCALE, y * ORBIT_SCALE, 0.0])


def _build_orbit_base():
    planet = Circle(radius=ORBIT_PLANET_RADIUS * ORBIT_SCALE, color=BLUE_D, fill_color=BLUE_D, fill_opacity=0.6, stroke_color=WHITE)
    planet.move_to(ORBIT_CENTER)
    label = Text("Earth", font_size=16, color=WHITE).move_to(ORBIT_CENTER)
    return VGroup(planet, label)


def _build_trajectory(visual: dict):
    points, speeds, outcome = _simulate_launch(visual.get("angle_deg", 0), visual.get("speed_factor", 1.0))
    scene_points = [_sim_to_scene(x, y) for x, y in points]
    color = _color(visual.get("color"), BLUE)
    path = VMobject(color=color, stroke_width=5)
    path.set_points_as_corners(scene_points)
    dot = Dot(color=color, radius=0.07).move_to(scene_points[0])
    return path, dot, points, speeds, outcome


def _build_energy_axes():
    axes = Axes(
        x_range=[0, 1, 0.25], y_range=[*ENERGY_Y_RANGE, 0.5],
        x_length=ENERGY_X_LEN, y_length=ENERGY_Y_LEN,
        axis_config={"include_tip": False, "stroke_color": GRAY, "stroke_width": 2, "font_size": 16},
        y_axis_config={"numbers_to_include": np.arange(-1.0, 1.01, 0.5), "decimal_number_config": {"num_decimal_places": 1}},
    ).move_to(ENERGY_CENTER)
    zero_line = DashedLine(axes.coords_to_point(0, 0), axes.coords_to_point(1, 0), color=GRAY, stroke_width=1.5)
    x_label = Text("time during flight →", font_size=14, color=GRAY).next_to(axes, DOWN, buff=0.12)
    y_label = Text("energy (relative units)", font_size=14, color=GRAY).next_to(axes, UP, buff=0.1).align_to(axes, LEFT)
    return VGroup(axes, zero_line, x_label, y_label), axes


def _energy_series(points, speeds, gm: float = GM):
    n = len(points)
    ts = [i / (n - 1) for i in range(n)]
    kes = [0.5 * v * v for v in speeds]
    pes = [-gm / math.hypot(x, y) for x, y in points]
    totals = [k + p for k, p in zip(kes, pes)]
    return ts, kes, pes, totals


def _curve_from_series(axes, ts, values, color, stroke_width=4):
    pts = [axes.coords_to_point(t, max(ENERGY_Y_RANGE[0], min(ENERGY_Y_RANGE[1], v))) for t, v in zip(ts, values)]
    curve = VMobject(color=color, stroke_width=stroke_width)
    curve.set_points_as_corners(pts)
    return curve, pts


def _build_energy_legend():
    rows = [(KE_COLOR, "Motion energy"), (PE_COLOR, "Gravity's pull"), (YELLOW, "Total energy")]
    items = VGroup()
    for color, label in rows:
        swatch = Line(LEFT * 0.25, RIGHT * 0.25, color=color, stroke_width=5)
        text = Text(label, font_size=16, color=WHITE)
        row = VGroup(swatch, text).arrange(RIGHT, buff=0.15)
        items.add(row)
    items.arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    items.move_to(LEGEND_POS)
    return items


def _tracer_updater(scene_points):
    def updater(mob, alpha):
        idx = min(len(scene_points) - 1, int(alpha * (len(scene_points) - 1)))
        mob.move_to(scene_points[idx])
        return mob

    return updater


def _build_formula_panel(legend, launch_index: int, color):
    """Symbolic (not numeric) formulas for the launch currently playing. Physics derivations
    reason in variables, not plugged-in decimals, so v_n stays a symbol throughout."""
    n = launch_index
    ke_row = MathTex(f"KE = \\tfrac{{1}}{{2}}mv_{{{n}}}^2", color=KE_COLOR, font_size=22)
    pe_row = MathTex("PE = -\\dfrac{GMm}{R}", color=PE_COLOR, font_size=22)
    total_row = MathTex(f"E_{{{n}}} = \\tfrac{{1}}{{2}}mv_{{{n}}}^2 - \\dfrac{{GMm}}{{R}}", color=color, font_size=22)
    panel = VGroup(ke_row, pe_row, total_row).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
    panel.next_to(legend, DOWN, buff=0.4).align_to(legend, LEFT)
    return panel


def _formula_text(latex: str):
    return _safe_mathtex(latex, color=YELLOW, font_size=44).move_to(FORMULA_POS)


class ProblemScene(Scene):
    def construct(self):
        spec_path = os.environ["STEPS_JSON"]
        spec = json.loads(open(spec_path).read())

        header = Text(spec["header_label"], font_size=22, color=GRAY).to_corner(UL)
        self.add(header)

        segments = spec["segments"]
        current_group = VGroup()  # fades out every iteration (the per-step panel/visual)
        orbit_group = VGroup()  # persists across a consecutive run of orbit_launch steps
        graph_group = VGroup()  # persists across a consecutive run of function_graph steps
        fbd_group = VGroup()  # persists while later steps derive formulas from the same diagram
        energy_axes = None
        launch_index = 0  # increments per real launch within a sequence -> v_1, v_2, v_3 symbols
        transient_energy = VGroup()  # this launch's KE/PE curves + tracer dots; replaced each launch

        for idx, segment in enumerate(segments):
            visual = segment.get("visual") or {}
            vtype = visual.get("type")
            duration = float(segment["duration"])
            prev_vtype = (segments[idx - 1].get("visual") or {}).get("type") if idx > 0 else None

            self.play(FadeOut(current_group), run_time=0.3)
            if prev_vtype == "orbit_launch" and vtype != "orbit_launch":
                self.play(FadeOut(orbit_group), FadeOut(transient_energy), run_time=0.4)
                orbit_group = VGroup()
                energy_axes = None
                launch_index = 0
                transient_energy = VGroup()
            if prev_vtype == "function_graph" and vtype != "function_graph":
                self.play(FadeOut(graph_group), run_time=0.4)
                graph_group = VGroup()
            # A formula/text-only step (vtype is None — no dedicated visual) does NOT count
            # as "something else": it's meant to derive a result FROM the diagram still on
            # screen, so the diagram only fades when a genuinely different visual follows.
            if len(fbd_group) > 0 and vtype not in (None, "free_body_diagram"):
                self.play(FadeOut(fbd_group), run_time=0.4)
                fbd_group = VGroup()

            if vtype == "vector_path":
                plot_group, axes, arrows, labels, resultant_line, resultant_label = _build_vector_path(visual)
                text_panel = _text_panel(segment, font_size=26).scale(0.85).to_edge(RIGHT, buff=0.5)
                current_group = VGroup(plot_group, text_panel)
                _check_no_overlap(plot_group, text_panel, f"step {idx} (vector_path)")

                num_phases = 1 + len(arrows) + (1 if resultant_line is not None else 0)
                total_anim_time = min(2.8, max(1.2, duration * 0.6))
                per_step = total_anim_time / num_phases
                self.play(Create(axes), FadeIn(text_panel), run_time=per_step)
                for arrow, label in zip(arrows, labels):
                    self.play(GrowArrow(arrow), FadeIn(label), run_time=per_step)
                if resultant_line is not None:
                    self.play(Create(resultant_line), FadeIn(resultant_label), run_time=per_step)
                anim_time = total_anim_time

            elif vtype == "circular_path":
                plot_group, arc, moving_dot, chord, chord_label = _build_circular_path(visual)
                text_panel = _text_panel(segment, font_size=26).scale(0.85).to_edge(RIGHT, buff=0.5)
                current_group = VGroup(plot_group, text_panel)
                _check_no_overlap(plot_group, text_panel, f"step {idx} (circular_path)")

                total_anim_time = min(3.0, max(1.4, duration * 0.6))
                has_second_phase = chord is not None or chord_label is not None
                trace_time = total_anim_time * 0.7 if has_second_phase else total_anim_time
                self.play(FadeIn(text_panel), Create(arc), MoveAlongPath(moving_dot, arc), run_time=trace_time)
                if chord is not None:
                    self.play(Create(chord), FadeIn(chord_label), run_time=total_anim_time - trace_time)
                elif chord_label is not None:
                    self.play(FadeIn(chord_label), run_time=total_anim_time - trace_time)
                anim_time = total_anim_time

            elif vtype == "function_graph":
                text_panel = _text_panel(segment, font_size=26).scale(0.85).to_edge(RIGHT, buff=0.5)
                reuse_graph = visual.get("keep_previous") and len(graph_group) > 0

                if not reuse_graph and len(graph_group) > 0:
                    self.play(FadeOut(graph_group), run_time=0.3)
                    graph_group = VGroup()

                if reuse_graph:
                    _check_no_overlap(graph_group, text_panel, f"step {idx} (function_graph, reused)")
                    anim_time = min(1.0, max(0.4, duration * 0.3))
                    self.play(FadeIn(text_panel), run_time=anim_time)
                else:
                    plot_group, base, curve_entries = _build_function_graph(visual)
                    graph_group.add(plot_group)
                    _check_no_overlap(plot_group, text_panel, f"step {idx} (function_graph)")
                    total_anim_time = min(3.2, max(1.4, duration * 0.6))
                    per_step = total_anim_time / max(1, len(curve_entries) + 1)
                    self.play(Create(base), FadeIn(text_panel), run_time=per_step)
                    for curve, shade, label, tangent in curve_entries:
                        anims = [Create(curve)]
                        if shade is not None:
                            anims.append(FadeIn(shade))
                        if label is not None:
                            anims.append(FadeIn(label))
                        self.play(*anims, run_time=per_step)
                        if tangent is not None:
                            self.play(Create(tangent), run_time=min(1.0, per_step))
                    anim_time = total_anim_time

                current_group = text_panel

            elif vtype == "free_body_diagram":
                text_panel = _text_panel(segment, font_size=26).scale(0.85).to_edge(RIGHT, buff=0.5)
                reuse_fbd = visual.get("keep_previous") and len(fbd_group) > 0

                if reuse_fbd:
                    _check_no_overlap(fbd_group, text_panel, f"step {idx} (free_body_diagram, reused)")
                    anim_time = min(1.0, max(0.4, duration * 0.3))
                    self.play(FadeIn(text_panel), run_time=anim_time)
                else:
                    if len(fbd_group) > 0:
                        self.play(FadeOut(fbd_group), run_time=0.3)
                    fbd_group = _build_free_body_diagram(visual)
                    _check_no_overlap(fbd_group, text_panel, f"step {idx} (free_body_diagram)")
                    anim_time = min(2.0, max(1.0, duration * 0.5))
                    self.play(FadeIn(fbd_group), FadeIn(text_panel), run_time=anim_time)

                current_group = text_panel

            elif vtype == "reference_frames":
                plot_group = _build_reference_frames(visual)
                text_panel = _text_panel(segment, font_size=26).scale(0.85).to_edge(RIGHT, buff=0.5)
                current_group = VGroup(plot_group, text_panel)
                _check_no_overlap(plot_group, text_panel, f"step {idx} (reference_frames)")
                anim_time = min(2.0, max(1.0, duration * 0.5))
                self.play(FadeIn(plot_group), FadeIn(text_panel), run_time=anim_time)

            elif vtype == "orbit_launch":
                formula = _formula_text(segment["latex"]) if segment.get("latex") else None
                total_anim_time = min(3.6, max(1.8, duration * 0.68))
                intro_time = min(0.6, total_anim_time * 0.2)

                if transient_energy:
                    self.play(FadeOut(transient_energy), run_time=0.3)
                    transient_energy = VGroup()

                intro_anims = [FadeIn(formula)] if formula is not None else []
                if prev_vtype != "orbit_launch":
                    base = _build_orbit_base()
                    energy_axes_group, energy_axes = _build_energy_axes()
                    legend = _build_energy_legend()
                    orbit_group.add(base, energy_axes_group, legend)
                    intro_anims += [Create(base), Create(energy_axes_group), FadeIn(legend)]
                if intro_anims:
                    self.play(*intro_anims, run_time=intro_time)

                if visual.get("no_trajectory"):
                    anim_time = total_anim_time
                else:
                    launch_index += 1
                    travel_time = total_anim_time - intro_time
                    path, dot, points, speeds, outcome = _build_trajectory(visual)
                    color = _color(visual.get("color"), BLUE)
                    ts, kes, pes, totals = _energy_series(points, speeds)
                    ke_curve, ke_pts = _curve_from_series(energy_axes, ts, kes, KE_COLOR)
                    pe_curve, pe_pts = _curve_from_series(energy_axes, ts, pes, PE_COLOR)
                    total_curve, total_pts = _curve_from_series(energy_axes, ts, totals, color, stroke_width=5)
                    ke_tracer = Dot(color=KE_COLOR, radius=0.06).move_to(ke_pts[0])
                    pe_tracer = Dot(color=PE_COLOR, radius=0.06).move_to(pe_pts[0])
                    v_label = MathTex(f"v_{{{launch_index}}}", color=color, font_size=22)
                    v_label.next_to(total_pts[-1], RIGHT, buff=0.1)
                    launch_tag = MathTex(f"v_{{{launch_index}}}", color=color, font_size=22)
                    launch_tag.next_to(path.get_start(), UP, buff=0.15)
                    formula_panel = _build_formula_panel(legend, launch_index, color)

                    orbit_group.add(path, dot, total_curve, v_label)
                    transient_energy = VGroup(ke_curve, pe_curve, ke_tracer, pe_tracer, launch_tag, formula_panel)
                    self.play(
                        Create(path), MoveAlongPath(dot, path),
                        Create(ke_curve), Create(pe_curve), Create(total_curve),
                        UpdateFromAlphaFunc(ke_tracer, _tracer_updater(ke_pts)),
                        UpdateFromAlphaFunc(pe_tracer, _tracer_updater(pe_pts)),
                        FadeIn(launch_tag), FadeIn(v_label), FadeIn(formula_panel),
                        run_time=travel_time, rate_func=lambda t: t,
                    )
                    anim_time = total_anim_time

                current_group = formula if formula is not None else VGroup()

            elif len(fbd_group) > 0:
                # A formula/derivation step with no visual of its own, but a diagram from an
                # earlier step is still active — keep showing that diagram and place this
                # step's text/formula beside it (right side), instead of fading to a blank
                # centered slide. This is what "derive the formula from the visual, don't
                # just state it cold" actually requires once the derivation spans several steps.
                text_panel = _text_panel(segment, font_size=26).scale(0.85).to_edge(RIGHT, buff=0.5)
                _check_no_overlap(fbd_group, text_panel, f"step {idx} (formula beside diagram)")
                anim_time = min(0.8, max(0.3, duration * 0.3))
                self.play(FadeIn(text_panel), run_time=anim_time)
                current_group = text_panel

            else:
                # Fallback for content with neither a dedicated visual primitive nor a formula
                # (e.g. plain conceptual narration steps in older vector_path-style videos).
                # Must show *something* here, or the screen goes black while the narration
                # plays with nothing to anchor it to.
                if segment.get("latex"):
                    current_group = _safe_mathtex(segment["latex"], color=YELLOW, font_size=44).move_to(DOWN * 0.3)
                    anim_time = min(0.8, max(0.3, duration * 0.3))
                    self.play(FadeIn(current_group), run_time=anim_time)
                elif segment.get("display_text"):
                    current_group = _text_panel(segment, font_size=34 if vtype != "intro" else 32)
                    current_group.move_to(DOWN * 0.3)
                    # Long problem statements wrap to many lines; centering alone can push the
                    # top (the segment's "label", e.g. "Problem") up into the header's space.
                    if current_group.get_top()[1] > 2.8:
                        current_group.shift(DOWN * (current_group.get_top()[1] - 2.8))
                    anim_time = min(0.8, max(0.3, duration * 0.3))
                    self.play(FadeIn(current_group), run_time=anim_time)
                else:
                    current_group = VGroup()
                    anim_time = 0.0

            remaining = max(0.1, duration - anim_time)
            self.wait(remaining)

        self.play(FadeOut(current_group), FadeOut(orbit_group), FadeOut(transient_energy), FadeOut(header), run_time=0.5)
