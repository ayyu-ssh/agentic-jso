def _group_or(values):
    cleaned = [str(value).strip() for value in (values or []) if str(value).strip()]
    if not cleaned:
        return ""
    quoted = " OR ".join([f'"{value}"' for value in cleaned])
    return f"({quoted})"


def _build_site_query(site, canonical):
    parts = [f"site:{site}"]

    roles_group = _group_or(canonical.get("roles"))
    skills_group = _group_or(canonical.get("skills"))
    domains_group = _group_or(canonical.get("domains"))
    location_group = _group_or(canonical.get("location"))
    intent_group = _group_or(canonical.get("intent"))

    for group in [roles_group, skills_group, domains_group, location_group, intent_group]:
        if group:
            parts.append(group)

    return " ".join(parts)


def linkedin_xray(canonical):
    return _build_site_query("linkedin.com/jobs", canonical)

def greenhouse_xray(canonical):
    return _build_site_query("boards.greenhouse.io", canonical)

def lever_xray(canonical):
    return _build_site_query("jobs.lever.co", canonical)

def wellfound_xray(canonical):
    return _build_site_query("wellfound.com/jobs", canonical)