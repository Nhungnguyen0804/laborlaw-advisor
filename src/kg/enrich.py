import json


def enrich_graph_context(graph_data, chunks_json_path):
    with open(chunks_json_path, 'r', encoding='utf-8') as f:
        chunks_data = json.load(f)

    chunk_index = {
        chunk['chunk_id']: chunk
        for chunk in chunks_data['chunks']
    }

    enriched_graph = {
        'metadata': {
            'law_info': chunks_data['metadata'],
            'seed_count': graph_data['seed_count'],
            'node_count': graph_data['node_count'],
            'relationship_count': graph_data['relationship_count']
        },
        'nodes_with_context': [],
        'relationships_with_context': []
    }

    for node in graph_data['nodes']:
        chunk_ids = set()

        for rel in graph_data['relationships']:
            if rel['source'] == node['text'] or rel['target'] == node['text']:
                chunk_id = rel.get('properties', {}).get('chunk_id')

                if chunk_id:
                    chunk_ids.add(chunk_id)

        contexts = []

        for chunk_id in chunk_ids:
            if chunk_id in chunk_index:
                chunk = chunk_index[chunk_id]

                contexts.append({
                    'chunk_id': chunk_id,
                    'article': chunk['metadata'].get('article_num'),
                    'article_title': chunk['metadata'].get('article_title'),
                    'chapter': chunk['metadata'].get('chapter_num'),
                    'chapter_title': chunk['metadata'].get('chapter_title'),
                    'content': chunk.get('content_with_context', chunk['content'])
                })

        enriched_graph['nodes_with_context'].append({
            'text': node['text'],
            'entity_type': node['entity_type'],
            'legal_contexts': contexts
        })

    for rel in graph_data['relationships']:
        chunk_id = rel.get('properties', {}).get('chunk_id')
        context = None

        if chunk_id and chunk_id in chunk_index:
            chunk = chunk_index[chunk_id]

            context = {
                'chunk_id': chunk_id,
                'article': chunk['metadata'].get('article_num'),
                'chapter': chunk['metadata'].get('chapter_num'),
                'full_text': chunk.get('content_with_context')
            }

        enriched_graph['relationships_with_context'].append({
            'source': rel['source'],
            'source_type': rel['source_type'],
            'relation': rel['relation_type'],
            'target': rel['target'],
            'target_type': rel['target_type'],
            'legal_context': context
        })

    return enriched_graph


import json


def test_enrich_graph_context(graph_data, chunks_json_path):
    enriched = enrich_graph_context(graph_data, chunks_json_path)

    metadata = enriched.get("metadata", {})

    print(f"Law code: {metadata.get('law_info', {}).get('law_code')}")
    print(f"Law name: {metadata.get('law_info', {}).get('law_name')}")
    print(f"Seed count: {metadata.get('seed_count')}")
    print(f"Node count: {metadata.get('node_count')}")
    print(f"Relationship count: {metadata.get('relationship_count')}")

    nodes = enriched.get("nodes_with_context", [])

    print(f"Total enriched nodes: {len(nodes)}")

    nodes_with_context = 0

    for node in nodes:
        if node.get("legal_contexts"):
            nodes_with_context += 1

    print(f"Nodes with legal context: {nodes_with_context}/{len(nodes)}")

    for i, node in enumerate(nodes[:3], 1):
        print(f"NODE {i}")
        print(f"Text: {node['text']}")
        print(f"Entity type: {node['entity_type']}")
        print(f"Contexts found: {len(node['legal_contexts'])}")

        for ctx in node['legal_contexts'][:2]:
            print(f"Chunk ID: {ctx['chunk_id']}")
            print(f"Article: {ctx['article']}")
            print(f"Article title: {ctx['article_title']}")
            print(f"Chapter: {ctx['chapter']}")
            print(f"Chapter title: {ctx['chapter_title']}")

     

    rels = enriched.get("relationships_with_context", [])

    print(f"Total enriched relationships: {len(rels)}")

    rels_with_context = 0

    for rel in rels:
        if rel.get("legal_context"):
            rels_with_context += 1

    print(f"Relationships with context: {rels_with_context}/{len(rels)}")

    for i, rel in enumerate(rels[:5], 1):
        print(f"RELATIONSHIP {i}")

        print(
            f"{rel['source']} "
            f"--[{rel['relation']}]--> "
            f"{rel['target']}"
        )

        if rel['legal_context']:
            ctx = rel['legal_context']

            print(f"Chunk ID: {ctx['chunk_id']}")
            print(f"Article: {ctx['article']}")
            print(f"Chapter: {ctx['chapter']}")

            if ctx['full_text']:
                preview = ctx['full_text'].replace("\n", " ")
                print(f"full text: {preview}")
        else:
            print("k tim dc legal context")

        print()

    missing_chunk_count = 0

    for rel in graph_data['relationships']:
        chunk_id = rel.get('properties', {}).get('chunk_id')

        if chunk_id is None:
            missing_chunk_count += 1

    print(f"Relationships miss chunk_id: {missing_chunk_count}")

    output_path = "src/kg/enrich.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            enriched,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"Save: {output_path}")

    if nodes_with_context == 0:
        print(" node with cotext ")

    if rels_with_context == 0:
        print("0 rel with context")

    if nodes_with_context > 0 and rels_with_context > 0:
        print("enrich!")

    return enriched


import sys
import os

log_path = os.path.join(os.path.dirname(__file__), "expand.txt")
sys.stdout = open(log_path, "w", encoding="utf-8")

from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASS = os.getenv("NEO4J_PASS")

from src.neo4j.connection import get_driver

driver = get_driver(NEO4J_URI, NEO4J_USER, NEO4J_PASS)

ner_res_path = 'src/retrieval/rrf_ner.json'

with open(ner_res_path, 'r', encoding='utf-8') as f:
    ner_results = json.load(f)['results']

from src.kg.expand import get_seed_relationships, expand_graph
from src.utils.paths import LABORLAW_CHUNKS_JSON

graph = get_seed_relationships(driver, ner_results)

bfs_graph = expand_graph(
    driver,
    ner_results,
    method='bfs',
    max_depth=2,
    max_nodes=30
)

dfs_graph = expand_graph(
    driver,
    ner_results,
    method='dfs',
    max_depth=2,
    max_nodes=30
)

test_enrich_graph_context(bfs_graph, LABORLAW_CHUNKS_JSON)

print('dfs')

test_enrich_graph_context(dfs_graph, LABORLAW_CHUNKS_JSON)