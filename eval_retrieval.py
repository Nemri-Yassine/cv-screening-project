from chat import vector_store, filter_chain, build_filter, CATEGORIES

K = 5

# each question describes a profile without giving the category name,
# the expected category is the folder of the CVs we want to find

TEST_QUESTIONS = [
    ("someone who prepares financial statements and handles tax returns", "ACCOUNTANT"),
    ("a lawyer with litigation and contract drafting experience", "ADVOCATE"),
    ("a person experienced in crop production and farm management", "AGRICULTURE"),
    ("someone who worked in fashion merchandising and clothing retail", "APPAREL"),
    ("a painter or art instructor with gallery exhibitions", "ARTS"),
    ("a technician who repairs car engines and does vehicle diagnostics", "AUTOMOBILE"),
    ("an aircraft mechanic or pilot with FAA certifications", "AVIATION"),
    ("a bank teller or loan officer handling customer accounts", "BANKING"),
    ("a call center agent handling outsourced customer support", "BPO"),
    ("someone who finds new partnerships and grows market share", "BUSINESS-DEVELOPMENT"),
    ("a cook who manages a kitchen and creates menus", "CHEF"),
    ("a site supervisor managing building projects and contractors", "CONSTRUCTION"),
    ("an advisor who helps companies improve their processes", "CONSULTANT"),
    ("someone skilled in Photoshop and Illustrator for graphic design", "DESIGNER"),
    ("a social media and video content producer", "DIGITAL-MEDIA"),
    ("a mechanical engineer using AutoCAD and SolidWorks", "ENGINEERING"),
    ("a financial analyst doing budgeting and forecasting", "FINANCE"),
    ("a personal trainer who creates workout programs", "FITNESS"),
    ("a nurse with patient care and hospital experience", "HEALTHCARE"),
    ("someone who handles recruiting, payroll and employee relations", "HR"),
    ("a system administrator supporting networks and servers", "INFORMATION-TECHNOLOGY"),
    ("someone who writes press releases and manages media relations", "PUBLIC-RELATIONS"),
    ("a sales representative who meets revenue targets and closes deals", "SALES"),
    ("a teacher who prepares lessons for elementary school students", "TEACHER"),
]


def precision_at_k(documents, expected):
    # how many of the K candidates are from the right category
    return sum(doc.metadata["category"] == expected for doc in documents) / K


def reciprocal_rank(documents, expected):
    # 1 if the first candidate is right, 1/2 if it's the second one, ... 0 if none
    for rank, doc in enumerate(documents, start=1):
        if doc.metadata["category"] == expected:
            return 1 / rank
    return 0


def basic_search(question):
    return vector_store.similarity_search(question, k=K)


def advanced_search(question):
    filters = filter_chain.invoke({"question": question, "categories": CATEGORIES})
    return vector_store.similarity_search(filters.search_query, k=K, filter=build_filter(filters))


for name, search in [("basic", basic_search), ("advanced", advanced_search)]:
    precisions = []
    reciprocal_ranks = []

    for question, expected in TEST_QUESTIONS:
        documents = search(question)
        precisions.append(precision_at_k(documents, expected))
        reciprocal_ranks.append(reciprocal_rank(documents, expected))
        print(f"[{name}] {expected:<25} P@{K}={precisions[-1]:.2f}  RR={reciprocal_ranks[-1]:.2f}")

    print(f"\n==> {name} RAG : Precision@{K} = {sum(precisions) / len(precisions):.2f}"
          f" | MRR = {sum(reciprocal_ranks) / len(reciprocal_ranks):.2f}\n")
