#!/usr/bin/env python
"""
Seed data script for Agent Twitter.
Run this to populate the database with example posts.
"""
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import orchestrator


async def create_seed_data():
    """Create initial seed data for demo"""
    seed_posts = [
        {"text": "@grok explique la différence entre RAG et fine-tuning en 5 lignes"},
        {
            "text": "Je prépare un entretien. @factcheck détecte les incohérences dans ce pitch: \"Je suis expert en ML avec 10 ans d'expérience, j'ai travaillé sur des projets NLP et CV en même temps tout en étant doctorant en physique quantique\"",
        },
        {"text": "@writer propose 3 versions punchy de ce tweet: \"Le product management c'est comme être un chef d'orchestre mais pour des features logicielles\""},
        {"text": "@dev design l'API pour un système de notifications minimal qui doit gérer push, email et in-app"},
        {
            "text": "@summarizer tldr: Les IA génératives transforment le travail créatif en automatisant la production de contenu textuel, visuel et audio. Cela bouleverse les industries créatives mais crée aussi de nouvelles opportunités. Les entreprises doivent s'adapter rapidement pour rester compétitives.",
        },
        {"text": "@analyst fais une matrice avantages/risques sur ce choix: migrer notre stack technique de Node.js vers Rust pour des performances maximales"},
        {"text": "@researcher donne-moi un résumé sur l'état actuel de la fusion nucléaire"},
        {"text": "@coach J'ai du mal à rester motivé pour mes side projects. Des conseils ?"},
        {"text": "@grok @factcheck Les élections américaines de 2024 vont-elles impacter le marché crypto ?"},
        {"text": "@dev @writer J'ai besoin d'expliquer le pattern Circuit Breaker à mon équipe. Peux-tu me faire une explication claire avec un exemple en Python ?"},
    ]

    print(f"🌱 Creating {len(seed_posts)} seed posts...")
    for i, post_data in enumerate(seed_posts, 1):
        print(f"  [{i}/{len(seed_posts)}] {post_data['text'][:50]}...")
        await orchestrator.process_post(post_data["text"])
        await asyncio.sleep(0.3)

    print("✅ Seed data created successfully!")


if __name__ == "__main__":
    print("=" * 50)
    print("🌱 Agent Twitter - Seed Data Generator")
    print("=" * 50)
    print()
    asyncio.run(create_seed_data())
