from typing import Literal

from posthog.hogql import ast
from posthog.hogql.context import HogQLContext
from posthog.hogql.database import create_hogql_database
from posthog.hogql.parser import parse_expr
from posthog.hogql.printer import print_ast


# This is called only from "non-hogql-based" insights to translate HogQL expressions into ClickHouse SQL
# All the constant string values will be collected into context.values
def translate_hogql(query: str, context: HogQLContext, dialect: Literal["hogql", "clickhouse"] = "clickhouse") -> str:
    """Translate a HogQL expression into a Clickhouse expression. Raises if any placeholders found."""
    if query == "":
        raise ValueError("Empty query")

    try:
        # Create a fake query that selects from "events" to have fields to select from.
        context.database = context.database or create_hogql_database(context.team_id)
        select_query_ref = ast.SelectQueryRef(tables={"events": ast.TableRef(table=context.database.events)})
        node = parse_expr(query, no_placeholders=True)
        select_query = ast.SelectQuery(select=[node], ref=select_query_ref)
        return print_ast(node, context=context, dialect=dialect, stack=[select_query])

    except SyntaxError as err:
        raise ValueError(f"SyntaxError: {err.msg}")
    except NotImplementedError as err:
        raise ValueError(f"NotImplementedError: {err}")
