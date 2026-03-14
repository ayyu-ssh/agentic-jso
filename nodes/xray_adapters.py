def linkedin_xray(canonical):
    roles = " OR ".join([f'"{r}"' for r in canonical["roles"]])
    skills = " OR ".join(canonical["skills"])

    query = f'site:linkedin.com/jobs ({roles}) ({skills})'
    return query

def greenhouse_xray(canonical):
    roles = " OR ".join([f'"{r}"' for r in canonical["roles"]])

    query = f'site:boards.greenhouse.io ({roles})'
    return query

def lever_xray(canonical):
    roles = " OR ".join([f'"{r}"' for r in canonical["roles"]])

    query = f'site:jobs.lever.co ({roles})'
    return query

def wellfound_xray(canonical):
    roles = " OR ".join([f'"{r}"' for r in canonical["roles"]])

    query = f'site:wellfound.com/jobs ({roles})'
    return query