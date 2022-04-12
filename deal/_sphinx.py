from __future__ import annotations

from typing import TYPE_CHECKING

from . import introspection


if TYPE_CHECKING:
    from sphinx.application import Sphinx as SphinxApp
    from sphinx.ext.autodoc import Options


CLASSIC_CONTRACTS = (introspection.Pre, introspection.Post, introspection.Ensure)


def autodoc(app: SphinxApp) -> None:
    """
    Activate the hook for [sphinx] that includes contracts into
    documentation generated by [autodoc].

    [sphinx]: http://www.sphinx-doc.org/
    [autodoc]: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
    """
    assert 'sphinx.ext.autodoc' in app.extensions
    app.connect('autodoc-process-docstring', _process_docstring)


def _process_docstring(
    app: SphinxApp,
    what: str,
    name: str,
    obj,
    options: Options,
    lines: list[str],
) -> None:
    raises: dict[str, str] = dict()
    contracts: list[str] = []
    examples: list[str] = []
    for contract in introspection.get_contracts(obj):
        if isinstance(contract, introspection.Raises):
            for exc in contract.exceptions:
                raises.setdefault(exc.__qualname__, '')
            continue

        if isinstance(contract, introspection.Reason):
            message = contract.message or f'``{contract.source}``'
            raises[contract.event.__qualname__] = message
            continue

        if isinstance(contract, CLASSIC_CONTRACTS):
            message = contract.message or f'``{contract.source}``'
            contracts.append(f'  * {message}')
            continue

        if isinstance(contract, introspection.Has):
            lines.append(':side-effects:')
            lines.extend(f'  * {m}' for m in contract.markers)
            continue

        if isinstance(contract, introspection.Example):
            examples.append(f'  * ``{contract.source}``')
            continue

        raise RuntimeError('unreachable')

    for exc_name, descr in sorted(raises.items()):
        lines.append(f':raises {exc_name}: {descr}')
    if contracts:
        lines.append(':contracts:')
        lines.extend(contracts)
    if examples:
        lines.append(':examples:')
        lines.extend(examples)
