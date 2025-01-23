from typing import Callable, Any

BaseFxn = Callable[[], str]
TokenFxn = Callable[[], str]
GetVarFxn = Callable[[str], None]
StoreVarFxn = Callable[[str, Any], None]