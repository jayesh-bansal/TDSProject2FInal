from ga1 import GA1_2, GA1_3, GA1_4, GA1_5, GA1_6, GA1_7, GA1_8, GA1_9, GA1_10, GA1_11, GA1_12, GA1_14, GA1_15, GA1_16, GA1_17, GA1_18
from ga2 import GA2_2, GA2_9
import uvicorn
from multiprocessing import Process

def run_api(port):
    """Function to run FastAPI without blocking execution."""
    uvicorn.run("main:app", host="0.0.0.0", port=port)

def fetch_answer(task_id, question, file_path):
    # if task_id == 'GA1.1': extract from excel
    if task_id == 'GA1.2':
        answer = GA1_2(question)
    if task_id == 'GA1.3':
        answer = GA1_3(file_path)
    if task_id == 'GA1.4':
        answer = GA1_4(question)
    if task_id == 'GA1.5':
        answer = GA1_5(question)
    if task_id == 'GA1.6':
        answer = GA1_6(question, file_path)
        # answer = GA1_6("https://exam.sanand.workers.dev/tds-2025-01-ga1","")
    if task_id == 'GA1.7':
        answer = GA1_7(question)
    if task_id == 'GA1.8':
        answer = GA1_8(question, file_path)
    if task_id == 'GA1.9':
        answer = GA1_9(question)
    if task_id == 'GA1.10':
        answer = GA1_10(file_path)
    if task_id == 'GA1.11':
        answer = GA1_11(question, file_path)
        # answer = GA1_11("https://exam.sanand.workers.dev/tds-2025-01-ga1","")
    if task_id == 'GA1.12':
        answer = GA1_12(question, file_path)
    # if task_id == 'GA1.13': extract from excel
    if task_id == 'GA1.14':
        answer = GA1_14(question, file_path)
    if task_id == 'GA1.15':
        answer = GA1_15(question, file_path)
    if task_id == 'GA1.16':
        answer = GA1_16(file_path)
    if task_id == 'GA1.17':
        answer = GA1_17(question, file_path)
    if task_id == 'GA1.18':
        answer = GA1_18(question)
    if task_id == 'GA2.2':
        answer = GA2_2(file_path)
    # if task_id == 'GA2.9':
    #     port = 9000
    #     process = Process(target=run_api, args=(port,))
    #     process.start()
    #     answer = GA2_9(file_path,port)
    #     # process.terminate()
    return answer
