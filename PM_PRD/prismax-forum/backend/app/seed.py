"""Seed the database with the prototype's content.

Idempotent: running it again does nothing unless --reset is passed.

    python -m app.seed            # seed if empty
    python -m app.seed --reset    # wipe content and reseed
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from .db import Base, SessionLocal, engine, init_db
from .models import Comment, Like, Save, Thread, User


def _txt(s: str) -> dict:
    return {"type": "p", "html": s, "text": s, "caption": "", "src": None}


def _h2(s: str) -> dict:
    return {"type": "h2", "html": s, "text": s, "caption": "", "src": None}


def _quote(s: str) -> dict:
    return {"type": "quote", "html": s, "text": s, "caption": "", "src": None}


def _img(src: str, caption: str) -> dict:
    return {"type": "image", "html": "", "text": "", "caption": caption, "src": src}


# The featured essay (from the prototype article view).
ESSAY = [
    _txt(
        'In the evolving landscape of digital interaction, we find ourselves '
        'increasingly inhabiting "Cognitive Silos" — spaces defined not just by the '
        "algorithms that feed us information, but by the structural limitations of the "
        "interfaces we use to engage with one another."
    ),
    _img("/assets/spiral.png", "Fig 1.1: Visualization of information nodes within a decentralized network."),
    _h2("The Illusion of Connectivity"),
    _txt(
        "While the immediate assumption is that more nodes lead to more diverse thought, "
        'the reality is a sharpening of boundaries. We are building "Digital Monographs" '
        "of our own identities, curating threads that reflect back a polished version of "
        "our existing biases."
    ),
    _quote("The compression of nuance into short-form interaction."),
    _quote('The prioritization of "Engagement" over "Understanding".'),
    _quote("The erosion of shared contextual foundations."),
    _txt(
        "To break these silos, we must return to deliberate, high-fidelity discourse. This "
        "means valuing the slow interaction — the long-form post, the referenced critique, "
        "and the intellectual humility to be proven wrong."
    ),
]


def _body(*paras: str) -> list[dict]:
    return [_txt(p) for p in paras]


# external_id, name, avatar_color
USERS = [
    ("demo:you", "You", "#8C7355"),
    ("demo:thorne", "Dr. Thorne", "#C08457"),
    ("demo:nakamura", "M. Nakamura", "#6E8B7A"),
    ("demo:vance", "Dr. L. Vance", "#9A7AA0"),
    ("seed:al-fayed", "S. Al-Fayed", "#B07A5A"),
    ("seed:archive", "Archive Team", "#7A8BA0"),
    ("seed:editorial", "Editorial", "#A07A7A"),
    ("seed:elias", "Elias Kael", "#8C7355"),
    ("seed:marcus", "Marcus J.", "#6E8B7A"),
    ("seed:sarah", "Sarah Drasner", "#9A7AA0"),
]

# Oct 2025 dates so cards render "Oct 24" etc.
_Y = 2025


def _dt(month: int, day: int) -> datetime:
    return datetime(_Y, month, day, 12, 0, tzinfo=timezone.utc)


# author_ext, title, category, excerpt, accent, badge, seed_likes, seed_comments,
# cover, content, date(m,d)
THREADS = [
    dict(
        author="demo:thorne",
        title="The Ontology of Autonomous Systems: Beyond Kinetic Response",
        category="Featured",
        excerpt="How do we define intent in a non-biological actor? This thread examines the philosophical frameworks required for true machine agency.",
        accent=True, badge=None, seed_likes=842, seed_comments=124,
        cover=None, content=ESSAY, date=(10, 24),
    ),
    dict(
        author="demo:nakamura",
        title="Architectural Latency: Designing Spaces for Hybrid Occupancy",
        category="Architecture",
        excerpt="A discussion on how commercial interiors must evolve to accommodate both human staff and mobile robotic units without friction.",
        accent=False, badge=None, seed_likes=312, seed_comments=56,
        cover=None,
        content=_body(
            "As robotic units move from the factory floor into shared commercial space, the "
            "buildings we design must negotiate two very different kinds of occupant.",
            "Hybrid occupancy is less about wider corridors and more about predictable "
            "geometry — surfaces and sightlines a machine can parse as confidently as a person.",
        ),
        date=(10, 22),
    ),
    dict(
        author="seed:al-fayed",
        title="Neural Drafting: The End of CAD?",
        category="Case Study",
        excerpt="Exploring generative spatial models replacing traditional software.",
        accent=False, badge="Case Study", seed_likes=204, seed_comments=38,
        cover="/assets/network.jpg",
        content=_body(
            "Generative spatial models now produce buildable geometry from a sentence of "
            "intent. Does the drafting table survive the transition?",
            "This case study walks through a studio that replaced its CAD pipeline with a "
            "neural drafting loop — and the surprising places where human revision still wins.",
        ),
        date=(10, 20),
    ),
    dict(
        author="seed:archive",
        title="Protocol 07: Standardizing Sensor Feedback Loops",
        category="Protocol",
        excerpt="Technical specifications and proposed standards for the next generation of core communication protocols.",
        accent=False, badge=None, seed_likes=201, seed_comments=89,
        cover=None,
        content=_body(
            "Protocol 07 proposes a common envelope for sensor feedback so that heterogeneous "
            "units can share a single perception bus.",
            "We outline the timing guarantees, the back-pressure model, and the migration path "
            "from the legacy point-to-point loops.",
        ),
        date=(10, 18),
    ),
    dict(
        author="demo:vance",
        title="Synthetic Synapses: Machine Learning vs Biological Logic",
        category="Research",
        excerpt="Contrasting the efficiency of neural networks with the robust adaptability of organic neural structures.",
        accent=False, badge=None, seed_likes=156, seed_comments=42,
        cover=None,
        content=_body(
            "Artificial networks optimize; biological ones adapt. The distinction matters more "
            "as we ask machines to operate in open, changing worlds.",
            "We compare sample efficiency, failure modes, and the energy cost of each approach — "
            "and ask what a genuinely hybrid architecture would require.",
        ),
        date=(10, 15),
    ),
    dict(
        author="seed:editorial",
        title="The Ethics of Remote Teleoperation in Combat Zones",
        category="Editorial",
        excerpt="A legal and moral framework for operators managing robots in hazardous geopolitical environments.",
        accent=False, badge=None, seed_likes=1100, seed_comments=210,
        cover=None,
        content=_body(
            "Distance changes responsibility. When an operator acts through a machine thousands "
            "of kilometres away, where does accountability actually sit?",
            "This editorial proposes a framework that keeps a clear human chain of responsibility "
            "without pretending the distance does not exist.",
        ),
        date=(10, 12),
    ),
]


def reset() -> None:
    Base.metadata.drop_all(bind=engine)
    init_db()


def seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        if db.scalar(select(Thread).limit(1)) is not None:
            print("Database already has threads; skipping. Use --reset to reseed.")
            return

        users: dict[str, User] = {}
        for ext, name, color in USERS:
            u = db.scalar(select(User).where(User.external_id == ext))
            if u is None:
                u = User(external_id=ext, name=name, avatar_color=color)
                db.add(u)
            users[ext] = u
        db.commit()
        for u in users.values():
            db.refresh(u)

        threads: dict[str, Thread] = {}
        for spec in THREADS:
            dt = _dt(*spec["date"])
            t = Thread(
                author_id=users[spec["author"]].id,
                title=spec["title"],
                category=spec["category"],
                excerpt=spec["excerpt"],
                cover_image=spec["cover"],
                content=spec["content"],
                status="published",
                accent=spec["accent"],
                badge=spec["badge"],
                seed_likes=spec["seed_likes"],
                seed_comments=spec["seed_comments"],
                created_at=dt,
                updated_at=dt,
                published_at=dt,
            )
            db.add(t)
            threads[spec["title"]] = t
        db.commit()

        # Comments on the featured thread (from the prototype discourse view).
        featured = threads[THREADS[0]["title"]]
        now = datetime.now(timezone.utc)
        c1 = Comment(
            thread_id=featured.id,
            author_id=users["seed:elias"].id,
            body='The concept of "slow interaction" is fascinating. In an era where latency is a '
            "technical sin, maybe intellectual latency is actually a virtue.",
            seed_likes=14,
            created_at=now - timedelta(hours=2),
        )
        db.add(c1)
        db.commit()
        db.refresh(c1)
        db.add(
            Comment(
                thread_id=featured.id,
                author_id=users["seed:marcus"].id,
                parent_id=c1.id,
                body='Exactly. The architecture of the "feed" is built for the scroll, not the '
                "pause. Prisma(x) seems to be pushing for the pause.",
                created_at=now - timedelta(hours=1),
            )
        )
        db.add(
            Comment(
                thread_id=featured.id,
                author_id=users["seed:sarah"].id,
                body="One thing missing here is the role of visual semiotics in these silos. It's "
                "not just the text, it's the branding of the silos themselves.",
                seed_likes=31,
                created_at=now - timedelta(hours=4),
            )
        )
        db.commit()
        print(f"Seeded {len(THREADS)} threads, {len(USERS)} users, 3 comments.")
    finally:
        db.close()


if __name__ == "__main__":
    if "--reset" in sys.argv:
        reset()
        print("Database reset.")
    seed()
