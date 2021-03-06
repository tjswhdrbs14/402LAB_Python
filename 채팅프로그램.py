# -*- coding:utf-8 -*-
import socketserver
import threading

HOST = '127.0.0.1'
PORT = 59850
lock = threading.Lock()  # syncronized 동기화 진행하는 스레드 생성


class UserManager:  # 사용자관리 및 채팅 메세지 전송을 담당하는 클래스
    # ① 채팅 서버로 입장한 사용자의 등록
    # ② 채팅을 종료하는 사용자의 퇴장 관리
    # ③ 사용자가 입장하고 퇴장하는 관리
    # ④ 사용자가 입력한 메세지를 채팅 서버에 접속한 모두에게 전송

    def __init__(self):
        self.users = {}  # 사용자의 등록 정보를 담을 사전 {사용자 이름:(소켓,주소),...}

    def addUser(self, username, conn, addr):  # 사용자 ID를 self.users에 추가하는 함수
        if username in self.users:  # 이미 등록된 사용자라면
            conn.send('이미 등록된 사용자입니다.\n'.encode())
            return None


                        # 새로운 사용자를 등록함
        lock.acquire()  # 스레드 동기화를 막기위한 락
        self.users[username] = (conn, addr)
        lock.release()  # 업데이트 후 락 해제

        self.sendMessageToAll('[%s]님이 입장했습니다.' % username)
        print('+++ 대화 참여자 수 [%d]' % len(self.users))

        return username

    def removeUser(self, username):  # 사용자를 제거하는 함수
        if username not in self.users:
            return

        lock.acquire()
        del self.users[username]
        lock.release()

        self.sendMessageToAll('[%s]님이 퇴장했습니다.' % username)
        print('--- 대화 참여자 수 [%d]' % len(self.users))
        return

    def messageHandler(self, username, msg):  # 전송한 msg를 처리하는 부분
        if msg[0] != '/':  # 보낸 메세지의 첫문자가 '/'가 아니면
            self.sendMessageToAll('[%s] %s' % (username, msg))
            return

        if msg.strip() == '/q':  # 보낸 메세지가 '/q'이면
            self.removeUser(username)
            return -1

        if msg.strip() == '/w':  # 보낸 메세지가 '/w'이면
            return 3

    def sendMessageToAll(self, msg):
        for conn, addr in self.users.values():
            conn.send(msg.encode())

class MyTcpHandler(socketserver.BaseRequestHandler):
    usermanager = UserManager()

    def handle(self):  # 클라이언트가 접속시 클라이언트 주소 출력
        print('[%s] 연결됨' % self.client_address[0])

        try:
            username = self.registerUsername()
            msg = self.request.recv(1024)
            while msg:
                print(msg.decode())
                if self.usermanager.messageHandler(username, msg.decode()) == -1:
                    self.request.close()
                    break
                if self.usermanager.messageHandler(username, msg.decode()) == 3:
                    self.Whisper(username, msg)
                    continue
                msg = self.request.recv(1024)

        except Exception as e:
            print(e)

        print('[%s] 접속종료' % self.client_address[0])
        self.usermanager.removeUser(username)

    def registerUsername(self):   # 사용자등록
        while True:
            self.request.send('로그인ID:'.encode())
            username = self.request.recv(1024)
            username = username.decode().strip()
            if self.usermanager.addUser(username, self.request, self.client_address):
                return username

    def Whisper(self, username, msg):  # 귓속말 함수 정의
        self.request.send('보낼 대상: '.encode())
        try:
            toUser = self.request.recv(1024)  #보낼 대상
            toUser = toUser.decode()
            if self.usermanager.users[toUser]:  # 대상이 등록되어 있으면
                self.request.send('귓속말: '.encode())
                msg = self.request.recv(1024)
                msg = msg.decode()
        except Exception as e:
            print(e)

        conn, addr = self.usermanager.users[toUser]  # conn = 대상의 소켓, addr = 대상의 주소
        msg = '<<%s>> %s' % (username, msg)
        conn.send(msg.encode())

class ChatingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):       # ThreadingMixIn: 쓰레드의 요청을 각각 처리해주는 클래스
    pass                                                                        # TCPServer


def runServer():
    print('+++ 채팅 서버를 시작합니다.')
    print('+++ 채팅 서버를 끝내려면 Ctrl-C를 누르세요.')

    try:
        server = ChatingServer((HOST, PORT), MyTcpHandler)
        server.serve_forever()  # shutdown이 나올때까지 계속 서비스(bind-listen-accept) 수행
    except KeyboardInterrupt:
        print('--- 채팅 서버를 종료합니다.')
        server.shutdown()
        server.server_close()


runServer()

