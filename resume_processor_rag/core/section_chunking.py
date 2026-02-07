def chunk_resume_sections(resume_text: str) -> list:
    """
    Split resume text into logical sections, then chunk further for EXPERIENCE and PROJECTS.
    Returns a list of plain text chunks for embedding.
    """
    import re

    # Define section headers to look for (order matters)
    SECTION_HEADERS = [
        ("EDUCATION", re.compile(r'^EDUCATION', re.I)),
        ("EXPERIENCE", re.compile(r'^EXPERIENCE', re.I)),
        ("TECHNICAL SKILLS", re.compile(r'^(TECHNICAL )?SKILLS', re.I)),
        ("PROJECTS", re.compile(r'^PROJECTS', re.I)),
        ("ADDITIONAL INFORMATION", re.compile(r'^(ADDITIONAL )?INFORMATION', re.I))
    ]

    # Split by lines and index all section headers
    lines = resume_text.splitlines()
    section_indices = []
    for idx, line in enumerate(lines):
        for header, pattern in SECTION_HEADERS:
            if pattern.match(line.strip()):
                section_indices.append((header, idx))

    # Add end of document boundary
    section_indices.append(('END', len(lines)))

    # Helper: further chunk projects by each project title
    def split_projects_chunk(section_lines):
        body = "\n".join(section_lines[1:]).strip()
        # Splits at each new project name (title line containing dash or colon and at least one capital)
        project_splits = re.split(
            r"(?=^[A-Z][\w .:/|–-]{3,100}[\-|:])", body, flags=re.MULTILINE
        )
        # Add header to each
        return [
            section_lines[0] + "\n" + proj.strip()
            for proj in project_splits if proj.strip()
        ]

    # Helper: further chunk experience by each job header (using '|', dates or similar)
    def split_experience_chunk(section_lines):
        body = "\n".join(section_lines[1:]).strip()
        job_splits = re.split(
            r"(?=^[\w .,&\-|]+(?:\|)[\w .,&\-\(\)]{2,}\d{4})", body, flags=re.MULTILINE
        )
        return [
            section_lines[0] + "\n" + job.strip()
            for job in job_splits if job.strip()
        ]

    # Chunk each section
    chunks = []
    count= 0
    #chunk = index, chunk_section_name, chunk_content
    for i in range(len(section_indices) - 1):
        count+=1
        every_chunk=[]
        section, start_idx = section_indices[i]
        end_idx = section_indices[i+1][1]
        section_lines = lines[start_idx:end_idx]
        section_text = "\n".join(section_lines).strip()
        if not section_text:
            continue
        every_chunk.append(count)
        every_chunk.append(start_idx)
        every_chunk.append(end_idx)
        every_chunk.append(section)
        if section == "PROJECTS":
            every_chunk.extend(split_projects_chunk(section_lines))
        elif section == "EXPERIENCE":
            every_chunk.extend(split_experience_chunk(section_lines))
        else:
            every_chunk.append(section_text)
        chunks.append(every_chunk)
    return chunks
