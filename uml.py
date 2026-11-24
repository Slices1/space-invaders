import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

FILL, EDGE = "#dae8fc", "#6c8ebf"
HEAD, ROW, PAD = 0.45, 0.3, 0.1

# name: (center x, top y, attributes, methods)
classes = {
    "GameObject": (6, 7.0, ["+ x, y", "+ active"], ["+ update()", "+ draw(painter)"]),
    "Player": (2, 4.3, ["+ SPEED", "+ lives"], ["+ move_left()", "+ move_right()", "+ shot()"]),
    "Bullet": (6, 4.3, ["+ owner"], ["+ update()", "+ draw(painter)"]),
    "Enemy": (10, 4.3, ["+ WIDTH, HEIGHT", "+ SPEED", "+ direction"], ["+ update()", "+ draw(painter)"]),
    "Boss": (10, 1.3, ["+ lives"], ["+ draw(painter)", "+ shot()"]),
    "World": (10, 11.0, ["+ score", "+ player", "+ objects"],
              ["+ create_enemies()", "+ add_object(obj)", "+ update()", "+ check_collisions()", "+ enemy_shoot()"]),
    "Game": (6, 12.2, ["+ world, view", "+ timer", "+ started"], ["+ game_loop()", "+ key_press(e)", "+ key_release(e)"]),
    "GameView": (2, 11.0, ["+ world", "+ game"], ["+ start_game()", "+ paintEvent(e)"]),
}

fig, ax = plt.subplots(figsize=(12, 13))
box = {}
for name, (cx, top, attrs, methods) in classes.items():
    w = max(len(s) for s in attrs + methods + [name]) * 0.1 + 0.5
    a_h, m_h = len(attrs) * ROW + PAD, len(methods) * ROW + PAD
    h = HEAD + a_h + m_h
    x = cx - w / 2
    box[name] = (x, top - h, w, h)
    ax.add_patch(Rectangle((x, top - h), w, h, fc="white", ec=EDGE, lw=1.2))
    ax.add_patch(Rectangle((x, top - HEAD), w, HEAD, fc=FILL, ec=EDGE, lw=1.2))
    ax.plot([x, x + w], [top - HEAD - a_h] * 2, color=EDGE, lw=1.2)
    ax.text(cx, top - HEAD / 2, name, ha="center", va="center", fontsize=10, weight="bold",
            style="italic" if name == "GameObject" else "normal")
    for i, s in enumerate(attrs + methods):
        y = top - HEAD - PAD / 2 - ROW * (i + 0.5) - (PAD if i >= len(attrs) else 0)
        ax.text(x + 0.12, y, s, va="center", fontsize=9)

def side(name, which):
    x, y, w, h = box[name]
    return {"top": (x + w / 2, y + h), "bottom": (x + w / 2, y),
            "left": x, "right": x + w}[which]

def edge(points, hollow):
    xs, ys = zip(*points)
    ax.plot(xs[:-1], ys[:-1], color="black", lw=1)
    style = "-|>,head_width=0.35,head_length=0.7" if hollow else "->,head_width=0.3,head_length=0.6"
    ax.annotate("", xy=points[-1], xytext=points[-2],
                arrowprops=dict(arrowstyle=style, fc="white", ec="black", lw=1, shrinkA=0, shrinkB=0))

# inheritance (orthogonal, merged like draw.io)
for child, parent in [("Player", "GameObject"), ("Bullet", "GameObject"), ("Enemy", "GameObject")]:
    (cx, cy), (px, py) = side(child, "top"), side(parent, "bottom")
    mid = (cy + py) / 2
    edge([(cx, cy), (cx, mid), (px, mid), (px, py)], True)
edge([side("Boss", "top"), side("Enemy", "bottom")], True)

# associations
edge([(side("Game", "left"), 10.6), (side("GameView", "right"), 10.6)], False)
edge([(side("Game", "right"), 10.6), (side("World", "left"), 10.6)], False)
edge([(side("GameView", "right"), 9.6), (side("World", "left"), 9.6)], False)
wx, wy = side("World", "bottom")
gy = box["GameObject"][1] + box["GameObject"][3] / 2
edge([(wx, wy), (wx, gy), (side("GameObject", "right"), gy)], False)
ax.text(wx + 0.1, gy + 0.15, "objects  0..*", fontsize=8)

ax.set_xlim(0, 12.5)
ax.set_ylim(-0.6, 12.6)
ax.set_aspect("equal")
ax.axis("off")
plt.savefig("uml.png", dpi=120, bbox_inches="tight", facecolor="white")
