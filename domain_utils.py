"""Shared domain parsing helpers, configured not to fetch suffix lists at runtime."""
from __future__ import annotations

import ipaddress

try:
    import tldextract
    _EXTRACTOR = tldextract.TLDExtract(suffix_list_urls=())
except Exception:  # optional fallback keeps offline analysis usable
    tldextract = None
    _EXTRACTOR = None

_MULTI_LABEL_SUFFIXES = {
    "co.uk", "org.uk", "ac.uk", "gov.uk", "com.au", "net.au",
    "org.au", "co.in", "firm.in", "net.in", "org.in", "gen.in",
    "ind.in", "co.jp", "co.nz", "com.br", "com.cn", "com.sg",
    "com.my", "com.tr", "com.mx", "com.ar", "co.za", "com.tw",
}


def registered_domain(host: str) -> str:
    host = (host or "").strip().strip(".").lower()
    if not host:
        return ""
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass

    if _EXTRACTOR is not None:
        try:
            ext = _EXTRACTOR(host)
            result = ".".join(x for x in [ext.domain, ext.suffix] if x)
            if result:
                return result
        except Exception:
            pass

    parts = host.split(".")
    if len(parts) <= 2:
        return host
    last_two = ".".join(parts[-2:])
    if last_two in _MULTI_LABEL_SUFFIXES and len(parts) >= 3:
        return ".".join(parts[-3:])
    return last_two
