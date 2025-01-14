import logging

def filter_prepared_items(media_items, status):
    """
    Filters media items to include only those with any property name containing 'status' and value equal to the specified status.
    """
    try:
        prepared_items = []
        for item in media_items:
            for key, value in item.items():
                if 'status' in key and value == status:
                    prepared_items.append(item)
                    break  # No need to check other properties if we found a match
        logging.info(f"Filtered items count: {len(prepared_items)} out of {len(media_items)}")
        return prepared_items
    except Exception as e:
        logging.error(f"Error filtering media items: {e}", exc_info=True)
        return []