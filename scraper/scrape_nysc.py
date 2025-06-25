import os
def scrape_nysc(year:str) -> str:
    filename = f"nysc_data_{year}.csv"
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("Batch,Programme,Institution,Course,S/No,Surname,Other Names,Gender,Course Name,Status\n")
        f.write(f"A, {year}, Dummy College, Dummy Course, 1, DOE, JOHN, M, Dummy Course, Registered\n")
    return filename