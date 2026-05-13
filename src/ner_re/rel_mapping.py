ENT_TYPE_PAIR_TO_REL_MAP = {
    ('LEGAL_ROLE', 'OBLIGATION'): 'requires', 
    ('LEGAL_ROLE', 'RIGHT'): 'enables', 
    ('LEGAL_ROLE', 'PROHIBITION'): 'prohibits',
    ('LEGAL_ROLE', 'ACTION'): 'involves', 
    ('LEGAL_ROLE', 'PROCEDURE'): 'requires',
    ('LEGAL_ROLE', 'PENALTY'): 'results_in',
    ('LEGAL_ROLE', 'LEGAL_CONCEPT'): 'involves',
    ('LEGAL_ROLE', 'LEGAL_REF'): 'applies_to', 
    ('LEGAL_ROLE', 'CONDITION'): 'has_condition',
    ('LEGAL_ROLE', 'TIME_PERIOD'): 'applies_to',

    ('OBLIGATION', 'LEGAL_ROLE'): 'applies_to',
    ('RIGHT', 'LEGAL_ROLE'): 'applies_to',
    ('PROHIBITION', 'LEGAL_ROLE'): 'applies_to',
    ('ACTION', 'LEGAL_ROLE'): 'involves',
    ('PROCEDURE', 'LEGAL_ROLE'): 'requires',
    ('PENALTY', 'LEGAL_ROLE'): 'applies_to',
    ('LEGAL_CONCEPT', 'LEGAL_ROLE'): 'involves',
    ('CONDITION', 'LEGAL_ROLE'): 'applies_to',

    ('ACTION', 'CONDITION'): 'has_condition',
    ('ACTION', 'OBLIGATION'): 'requires',
    ('ACTION', 'RIGHT'): 'enables',
    ('ACTION', 'PENALTY'): 'results_in',
    ('ACTION', 'PROCEDURE'): 'involves',
    ('ACTION', 'LEGAL_CONCEPT'): 'involves',
    ('ACTION', 'TIME_PERIOD'): 'applies_to',

    ('CONDITION', 'ACTION'): 'applies_to',
    ('PENALTY', 'ACTION'): 'results_in',
    ('PROCEDURE', 'ACTION'): 'involves',
    ('TIME_PERIOD', 'ACTION'): 'applies_to',

    ('LEGAL_CONCEPT', 'LEGAL_CONCEPT'): 'related_to',
    ('LEGAL_CONCEPT', 'LEGAL_REF'): 'cites',
    ('LEGAL_CONCEPT', 'CONDITION'): 'has_condition',
    ('LEGAL_CONCEPT', 'OBLIGATION'): 'requires',
    ('LEGAL_CONCEPT', 'RIGHT'): 'enables',
    ('LEGAL_CONCEPT', 'PROHIBITION'): 'prohibits',
    ('LEGAL_CONCEPT', 'ACTION'): 'involves',

    ('LEGAL_REF', 'LEGAL_CONCEPT'): 'defines',
    ('LEGAL_REF', 'LEGAL_ROLE'): 'regulates',
    ('LEGAL_REF', 'OBLIGATION'): 'defines',
    ('LEGAL_REF', 'RIGHT'): 'defines',
    ('LEGAL_REF', 'PROHIBITION'): 'prohibits',
    ('LEGAL_REF', 'PENALTY'): 'defines',
    ('LEGAL_REF', 'PROCEDURE'): 'defines',

    ('CONDITION', 'OBLIGATION'): 'enables',
    ('CONDITION', 'RIGHT'): 'enables',
    ('CONDITION', 'PROHIBITION'): 'enables',
    ('CONDITION', 'PENALTY'): 'enables',

    ('TIME_PERIOD', 'OBLIGATION'): 'applies_to',
    ('TIME_PERIOD', 'RIGHT'): 'applies_to',
    ('TIME_PERIOD', 'PROCEDURE'): 'applies_to',
    ('TIME_PERIOD', 'LEGAL_CONCEPT'): 'applies_to',


    ('PROCEDURE', 'OBLIGATION'): 'requires',
    ('PROCEDURE', 'CONDITION'): 'has_condition',
    ('PROCEDURE', 'PENALTY'): 'results_in',


    ('PENALTY', 'OBLIGATION'): 'violates',
    ('PENALTY', 'PROHIBITION'): 'violates',

    # is connect true 
    ('LEGAL_ROLE', 'LEGAL_ROLE'): 'related_to',
    ('OBLIGATION', 'OBLIGATION'): 'related_to',
    ('RIGHT', 'RIGHT'): 'related_to',
    ('PROHIBITION', 'PROHIBITION'): 'related_to',
}

def get_relationship_type(ent_type_1, ent_type_2):
    ent_type_pair = (ent_type_1, ent_type_2)
    default_rel = 'related_to'
    rel_type = ENT_TYPE_PAIR_TO_REL_MAP.get(ent_type_pair, default_rel)
    return rel_type


def fill_missing_relationship_types(data):

    updated_types = []

    for doc in data:
        entities = {
            ent['id']: ent
            for ent in doc.get('entities', [])
        }

        for edge in doc.get('action_texts', []):

            # bỏ qua nếu đã có type
            if edge.get('edge_type'):
                continue

            source = entities.get(edge.get('source_entity'))
            target = entities.get(edge.get('target_entity'))

            if not source or not target:
                continue

            rel_type = get_relationship_type(
                source.get('type', 'UNKNOWN'),
                target.get('type', 'UNKNOWN')
            )

            edge['edge_type'] = rel_type #update 
            edge['edge_type_updated'] = True

            updated_types.append(rel_type)
    print(f'Đã update được {len(updated_types)}')
    return data

