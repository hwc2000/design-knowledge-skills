"""분산처리 지식트리 주제 → 설계 질문 태그. U=단원 기본값, OV=주제 이름 키워드 덮어쓰기.
새 강의(20강~)를 넣으면 U 에 그 강의 단원 태그 목록을 추가한다."""
import json, re, sys, collections
U={  # 강: 단원 순서대로 기본 태그
 3:['일관성','일관성','일관성','배경','일관성','배경'],
 4:['구조']*5,
 5:['통신','통신','통신','통신','통신','통신','통신','구조','구조'],
 6:['구조','구조','구조','찾기','찾기','구조','배경','구조'],
 7:['분할']*8+['배경'],
 8:['통신','통신','통신','배경','통신','통신','통신','성능','성능','성능','통신'],
 9:['통신']*7+['통신','통신','장애','통신'],
 10:['성능','성능','성능','성능','조정','통신','성능','배경'],
 11:['찾기'], 12:['순서'],
 13:['배경','순서','순서','충돌','순서','순서','순서'],
 14:['조정']*8+['배경'],
 15:['조정','조정','장애','장애','장애','장애','장애','조정','조정'],
 16:['복제','복제','일관성','일관성','일관성','일관성','일관성','일관성','일관성'],
 17:['일관성']*7,
 18:['충돌','충돌','충돌','복제','충돌','충돌','충돌'],
 19:['복제','복제','복제','복제','복제','일관성','복제','복제'],
 20:['배경','복제','복제','장애','일관성','복제','복제'],
}
OV=[  # 주제 이름 키워드 → 태그 (단원 기본값보다 우선)
 (r'다음 강의|오늘의 정리|오늘 정리|오늘 잡은|오늘의 핵심|마지막 한 줄|핵심 한 줄씩|^역사$|지난 시간|^결국, |오늘의 5가지|세 갈래 한 줄|통신은 계층으로|세 묶음으로 본 계층','배경'),
 (r'페일오버|SPOF|장애로 보면|토큰을 잃어버리면|타임아웃으로 정리|코디네이터가 죽으면','장애'),
 (r'at-most|at-least|exactly-once|실무의 정석','장애'),
 (r'Quorum: 과반|Anti-Entropy|리더 기반 vs 리더리스|불변 로그|복제되는 과정','복제'),
 (r'요청 라우팅|IPFS|Service Discovery','찾기'),
 (r'MVCC|병합|장바구니의 수렴','충돌'),
 (r'TrueTime|Spanner의 핵심|Total-Order Multicast가','순서'),
 (r'PACELC','일관성'),
 (r'락 기반 리더|외부 선출','조정'),
 (r'CDN','성능'),
 (r'TCP vs UDP','통신'),
 (r'Leader Epoch','장애'),          # 20강: 옛 리더 펜싱. 15강 '리더 에포크'(조정)는 건드리지 않게 영문 그대로
 (r'CockroachDB: 닫힌','일관성'),    # 20강: 팔로워 읽기. 13강 'CockroachDB'(순서)와 구분
 (r'etcd: 조건부','장애'),           # 20강: 재시도 멱등. 15강 'etcd: 리스'(조정)와 구분
]
# 보조 태그: 주제 이름에 이 낱말이 있으면 다른 스킬에도 '링크'를 건다 (본문은 주 태그 스킬에만 있음).
# 강의 번호와 상관없이 같은 규칙. 위에서부터 보고, 주 태그와 같은 스킬은 빼고 최대 2개.
SEE=[
 (r'[Ee]poch|에포크|펜싱|Fencing|세대 시계|세대 번호|Generation Clock|유령 리더|Zombie',['장애','조정']),
 (r'스플릿 브레인|Split Brain|Network Partition|네트워크 분할',['장애','복제']),
 (r'Quorum|N ?· ?W ?· ?R|W ?\+ ?R|W ?> ?N|과반|ONE vs QUORUM|Consistency Level|Tunable',['복제','일관성']),
 (r'페일오버|Failover|리더 교체|Primary 장애|리더 장애',['장애','조정']),
 (r'하트비트|Heartbeat|장애 감지|Failure Detector|φ',['조정','장애']),
 (r'High[- ]Water|HWM|Commit Index|커밋 인덱스|LEO',['일관성','복제']),
 (r'Raft|리더-팔로워|Leader-Follower|리더 기반|ISR',['복제','조정']),
 (r'Gossip|가십',['장애']),  # 복제 쪽은 Anti-Entropy 규칙이 맡는다
 (r'Anti-Entropy|Read Repair|읽기 복구|Hinted Handoff|Sloppy',['장애','일관성']),
 (r'at-most|at-least|exactly-once|전달 보장|멱등|Idempot|재시도|요청 ID',['통신','장애']),
 (r'2f ?\+ ?1|내결함성|장애를 견딘|로그 절단|Truncation',['장애']),
 (r'Kafka',['통신']),
 (r'Read-Your-Writes|내 쓰기|Monotonic|단조|[Ss]tale|오래된 읽기|Follower Reads|팔로워 읽기|세션 보장|버전 토큰|Session Stickiness',['일관성','복제']),
 (r'Eventual|최종 일관',['일관성']),
 (r'MVCC|스냅샷|닫힌 타임스탬프|Closed Timestamp|TrueTime|외부 일관성',['일관성','순서']),
 (r'Linearizab',['조정']),
 (r'Vector Clock|Version Vector|Lamport|HLC|논리 시계|happened-before',['순서']),
 (r'백프레셔|Backpressure|흐름 제어|완충',['성능']),
 (r'파이프라이닝|파이프라인(?! \(PUSH)|Pipeline|배칭',['성능']),  # ZeroMQ PUSH/PULL 패턴은 성능 기법이 아님
 (r'Replication|복제',['복제']),
 (r'Partitioning|파티션|샤딩|Sharding',['분할']),
 (r'ZooKeeper|etcd|Lease|리스\(|분산 락|락 기반|상호 배제',['조정']),
 (r'CAP|PACELC|ACID|BASE',['일관성']),
 (r'SPOF|단일 실패점',['구조','장애']),
 (r'Service Discovery|DNS',['찾기']),
 (r'CRDT|LWW|충돌 해소|병합',['충돌']),
]
def extras(title):
    """주제 이름 → 보조 태그 후보(순서대로, 중복 없이). 주 태그 제외·개수 제한은 build_skills 에서."""
    out=[]
    for pat,tgs in SEE:
        if re.search(pat,title):
            out+=[t for t in tgs if t not in out]
    return out
def tag(lec,ui,t):
    for pat,tg in OV:
        if re.search(pat,t): return tg
    return U[lec][ui]
def main():
    data=json.load(open(sys.argv[1]))
    cnt=collections.Counter(); where=collections.defaultdict(set); out=[]
    for x in data:
        out.append(f"\n## {x['lec']}강 · {x['title']}\n\n{'https://claude.ai/artifact/'+x['id']}\n")
        for ui,(u,ts) in enumerate(x['units']):
            if u: out.append(f"\n**{u}**\n")
            if not ts: ts=[u]
            for t in ts:
                t=re.sub(r'\s*p\.\d[\d–·, ]*$','',re.sub(r' · p\.\d[\d–]*$','',t)).strip()
                t=re.sub(r'([가-힣a-z)])([A-Z][a-z])',r'\1 \2',t) if x['lec']==4 else t
                g=tag(x['lec'],ui,t); cnt[g]+=1; where[g].add(x['lec'])
                out.append(f"- {t} `{g}`")
    open(sys.argv[2],'w').write('\n'.join(out)+'\n')
    for g,c in cnt.most_common(): print(g,c,sorted(where[g]))
    print('total',sum(cnt.values()))

if __name__=='__main__': main()
