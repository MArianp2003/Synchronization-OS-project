import threading, time, psutil, random

class BoundedBuffer:

    def __init__(self, size=5):
        self.size = size
        self.capacity = self.size
        self.filled = 0
        self.buffer = [0 for _ in range(size)]
        self.read_index = 0
        self.write_index = 0
        self.mutex = threading.Semaphore(1)
        self.empty = threading.Semaphore(self.size)
        self.full = threading.Semaphore(0)

    def write(self, message):
        self.buffer[self.write_index] = message
        print(f'message \"{message}\" was wrote in index {self.write_index} successfully')
        self.write_index = (self.write_index + 1) % self.size
        self.capacity -= 1
        self.filled += 1

    def check_write(self, message, nb=1):
        if nb:
            self.mutex.acquire()
            if self.capacity == 0:
                print('There is not enough space to write')
            else:
                self.write(message)
            self.mutex.release()
        else:
            self.empty.acquire()
            self.mutex.acquire()
            self.write(message)
            self.mutex.release()
            self.full.release()


    def read(self, reader):
        message = self.buffer[self.read_index]
        self.buffer[self.read_index] = 0
        if (reader != -1):
            print(f'message \"{message}\" was peak from index {self.read_index} successfully by \"{reader}\"')
        self.read_index = (self.read_index + 1) % self.size
        self.capacity += 1
        self.filled -= 1
        return message

    def check_read(self, reader, nb):
        if nb:
            self.mutex.acquire()
            if self.filled == 0:
                print('There is no item in the buffer')
            else:
                self.read(reader)
            self.mutex.release()
        else:
            self.full.acquire()
            self.mutex.acquire()
            self.read(reader)
            self.mutex.release()
            self.empty.release()
        
    def stats(self):
        self.mutex.acquire()
        print('Number of messages in the buffer:', self.filled)
        total = ''
        for message in self.buffer:
            if message != 0:
                total += message
        print('Total length of messages:', len(total))
        memory_usage = psutil.Process().memory_info().rss / (1024 ** 2), 'MB'
        print('Total memory usage:', memory_usage)
        self.mutex.release()
        return (self.size, len(total), memory_usage)

def send(thread_id, buffer: BoundedBuffer, times):
    for i in range(times):
        rc = random.choice([0, 1])
        buffer.check_write(f'writer{thread_id} message{i}', nb=bool(rc))
        time.sleep(0.1)

def get(thread_id, buffer: BoundedBuffer, times):
    for _ in range(times):
        rc = random.choice([0, 1])
        buffer.check_read(f'reader{str(thread_id)}' , nb=bool(rc))
        time.sleep(0.1)
        
def get_stats(times, buffer):
    for _ in range(times):
        buffer.stats()
        time.sleep(0.1)

def main():
    MAX_TIMES = 3
    MIN_TIMES = 1

    writer_num = int(input('Writers: '))
    reader_num = int(input('Readers: '))
    stats_num = int(input('Stats: '))
    size = int(input('Buffer size: '))
    buffer = BoundedBuffer(size)
    
    load = input('load? (0/1): ')
    if load == '1':
        with open('load.txt', 'r') as read_file:
            messages = read_file.readlines()
        for message in messages:
            buffer.check_write(message.strip(), nb=1)
    
    print('Benchmark:')
    writer_threads = []
    for i in range(writer_num):
        send_times = random.choice(list(range(MIN_TIMES, MAX_TIMES + 1)))
        print(f'writer id = {i} times = {send_times}')
        writer_threads.append(threading.Thread(target=send, args=(i, buffer, send_times)))
    
    reader_threads = []
    for i in range(reader_num):
        get_times = random.choice(list(range(MIN_TIMES, MAX_TIMES + 1)))
        print(f'reader id = {i} times = {get_times}')
        reader_threads.append(threading.Thread(target=get, args=(i, buffer, get_times)))

    stats_thread = threading.Thread(target=get_stats, args=(stats_num, buffer))
    all_threads = writer_threads + reader_threads + [stats_thread]
    random.shuffle(all_threads)

    for item in all_threads:
        item.start()
    for item in all_threads:
        item.join()

    load = input('load? (0/1): ')
    if load == '1':
        with open('load.txt', 'w') as write_file:
            filled = buffer.filled
            messages = [buffer.read(-1) for _ in range(filled)]
            for message in messages:
                write_file.write(f'{message}\n')
        print('messages saved successfully')

main()
