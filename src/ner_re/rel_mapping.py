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

    #bo sung thieu lan 1
    ('TIME_PERIOD', 'LEGAL_ROLE'): 'applies_to',
    ('RIGHT', 'TIME_PERIOD'): 'applies_to',
    ('LEGAL_CONCEPT', 'TIME_PERIOD'): 'applies_to',
    ('TIME_PERIOD', 'CONDITION'): 'applies_to',
    ('CONDITION', 'LEGAL_CONCEPT'): 'involves',
    # bo sung thieu lan 2
    ('PROHIBITION', 'PROHIBITION'): 'related_to',
    ('OBLIGATION', 'RIGHT'): 'related_to',
    ('OBLIGATION', 'PROHIBITION'): 'related_to',
    ('OBLIGATION', 'ACTION'): 'involves',
    ('OBLIGATION', 'PROCEDURE'): 'requires',
    ('OBLIGATION', 'PENALTY'): 'results_in',
    ('OBLIGATION', 'LEGAL_CONCEPT'): 'involves',
    ('OBLIGATION', 'LEGAL_REF'): 'cites',
    ('OBLIGATION', 'CONDITION'): 'has_condition',
    ('OBLIGATION', 'TIME_PERIOD'): 'applies_to', 
    ('RIGHT', 'OBLIGATION'): 'requires',
    ('RIGHT', 'PROHIBITION'): 'related_to',
    ('RIGHT', 'ACTION'): 'involves',
    ('RIGHT', 'PROCEDURE'): 'requires',
    ('RIGHT', 'PENALTY'): 'results_in',
    ('RIGHT', 'LEGAL_CONCEPT'): 'involves',
    ('RIGHT', 'LEGAL_REF'): 'cites',
    ('RIGHT', 'CONDITION'): 'has_condition',
    ('PROHIBITION', 'OBLIGATION'): 'related_to',
    ('PROHIBITION', 'RIGHT'): 'related_to',
    ('PROHIBITION', 'ACTION'): 'involves',
    ('PROHIBITION', 'PROCEDURE'): 'requires',
    ('PROHIBITION', 'PENALTY'): 'results_in',
    ('PROHIBITION', 'LEGAL_CONCEPT'): 'involves',
    ('PROHIBITION', 'LEGAL_REF'): 'cites',
    ('PROHIBITION', 'CONDITION'): 'has_condition',
    ('PROHIBITION', 'TIME_PERIOD'): 'applies_to',
    ('ACTION', 'PROHIBITION'): 'prohibits',
    ('ACTION', 'ACTION'): 'related_to',
    ('ACTION', 'LEGAL_REF'): 'cites',
    ('PROCEDURE', 'RIGHT'): 'enables',
    ('PROCEDURE', 'PROHIBITION'): 'prohibits',
    ('PROCEDURE', 'PROCEDURE'): 'related_to',
    ('PROCEDURE', 'LEGAL_CONCEPT'): 'involves',
    ('PROCEDURE', 'LEGAL_REF'): 'cites',
    ('PROCEDURE', 'TIME_PERIOD'): 'applies_to',
    ('PENALTY', 'RIGHT'): 'related_to',
    ('PENALTY', 'PROCEDURE'): 'requires',
    ('PENALTY', 'PENALTY'): 'related_to',
    ('PENALTY', 'LEGAL_CONCEPT'): 'involves',
    ('PENALTY', 'LEGAL_REF'): 'cites',
    ('PENALTY', 'CONDITION'): 'has_condition',
    ('PENALTY', 'TIME_PERIOD'): 'applies_to',
    ('LEGAL_CONCEPT', 'PROCEDURE'): 'involves',
    ('LEGAL_CONCEPT', 'PENALTY'): 'results_in',
    ('LEGAL_REF', 'ACTION'): 'defines',
    ('LEGAL_REF', 'LEGAL_REF'): 'related_to',
    ('LEGAL_REF', 'CONDITION'): 'defines',
    ('LEGAL_REF', 'TIME_PERIOD'): 'applies_to',
    ('CONDITION', 'PROCEDURE'): 'requires',
    ('CONDITION', 'LEGAL_REF'): 'cites',
    ('CONDITION', 'CONDITION'): 'related_to',
    ('CONDITION', 'TIME_PERIOD'): 'applies_to',
    ('TIME_PERIOD', 'PROHIBITION'): 'applies_to',
    ('TIME_PERIOD', 'PENALTY'): 'applies_to',
    ('TIME_PERIOD', 'LEGAL_REF'): 'cites',
    ('TIME_PERIOD', 'TIME_PERIOD'): 'related_to',
}

def get_relationship_type(ent_type_1, ent_type_2):
    ent_type_pair = (ent_type_1, ent_type_2)
    default_rel = 'related_to'
    rel_type = ENT_TYPE_PAIR_TO_REL_MAP.get(ent_type_pair, default_rel)
    return rel_type


def fill_missing_relationship_types(data,all_entities):
    # map tu all ent 
    entities = {}

    for ent in all_entities:
        entities[ent['id']] = ent

    updated_types = []

    for doc in data:
        for edge in doc.get('action_texts', []):

            # bỏ qua nếu đã có type
            if edge.get('edge_type') is not None:
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

