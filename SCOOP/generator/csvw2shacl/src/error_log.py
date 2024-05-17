
import os

def empty_error(logger):
    """Error: No tableSchema or tables found in CSVW file."""
    logger.error("No tableSchema or tables found in CSVW file")

def url_error_check(j, logger):
    """Error: The url property is required in a Table."""
    if j.get("url") == None:
        logger.error("The url property is required in a Table.")
        return False
    elif isinstance(j.get("url"), str) == False:
        logger.error("The url property must be a valid file path.")
        return False
    elif (isinstance(j.get("url"), str) == False) and (j.get("url").startswith("http") == False):
        logger.error("The url property must be a valid file path.")
        return False

def id_error_check(j, logger):
    """Error: @id must not start with _:."""
    if j.get("@id") and j.get("@id").startswith("_:"):
        logger.error("@id must not start with _:.")

def type_error_check(j, logger):
    """Error: @type must be a string."""
    if j.get("@type"):
        logger.error("@type must be a string.")

def tablesarray_error(logger):
    """Error: tables must be an array."""
    logger.error("tables must be an array.")