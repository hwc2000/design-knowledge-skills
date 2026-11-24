"""지식트리 주제 → 설계 질문 태그.
- 주 태그: 과목 설정(subjects/<과목>.json)의 단원별 tags 가 기본값, OV(주제 이름 낱말)가 덮어쓴다.
- 보조 태그: SEE(주제 이름 낱말 → 태그 목록). 다른 스킬에 링크만 남긴다.
OV·SEE 는 과목과 상관없이 모든 주제에 똑같이 걸린다. 새 규칙은 기존 주제를 먼저 검색하고 좁게 쓴다."""
import json, re, sys, collections
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
 (r'Read-Your-Writes|내 쓰기|Monotonic|단조|Stale Read|오래된 읽기|Follower Reads|팔로워 읽기|세션 보장|버전 토큰|Session Stickiness',['일관성','복제']),
 (r'Eventual|최종 일관',['일관성']),
 (r'MVCC|스냅샷|닫힌 타임스탬프|Closed Timestamp|TrueTime|외부 일관성',['일관성','순서']),
 (r'Linearizab',['조정']),
 (r'Vector Clock|Version Vector|Lamport|HLC|논리 시계|happened-before',['순서']),
 (r'백프레셔|Backpressure|흐름 제어|완충',['성능']),
 (r'파이프라이닝|(?<!관측 )파이프라인(?! \(PUSH)|Pipeline|배칭',['성능']),  # ZeroMQ PUSH/PULL 패턴은 성능 기법이 아님
 (r'Replication|복제',['복제']),
 (r'Partitioning|파티션|샤딩|Sharding',['분할']),
 (r'ZooKeeper|etcd|Lease|리스\(|분산 락|락 기반|상호 배제',['조정']),
 (r'CAP|PACELC|ACID|BASE',['일관성']),
 (r'SPOF|단일 실패점',['구조','장애']),
 (r'Service Discovery|DNS',['찾기']),
 (r'CRDT|LWW|충돌 해소|병합',['충돌']),
 # 인프라 계열 낱말 (2026-11-19). 분산처리 주제와 낱말이 달라도 같은 질문으로 잇는다
 (r'재해|GSLB|DR\)',['장애','복제']),
 (r'이중화',['장애']),  # 전원·NIC·스위치 이중화는 데이터 복제가 아니다
 (r'로드밸런|부하분산|부하 분산|L4 ?/ ?L7|Scale-?(out|up)|Scalab|확장|오토스케일|Stateless|세션 유지',['확장']),
 (r'헬스체크|Health ?[Cc]heck',['장애','확장']),
 (r'캐시|Cache|캐싱과|CDN|TTL|히트율',['성능','일관성']),  # '응답 캐싱'(멱등 수신자)은 캐시 설계가 아니다
 (r'모니터링|관측|Observab|알림 룰|메트릭|로그로|감사 로그',['관측']),
 (r'장애 주입|Chaos|카오스',['장애','관측']),
 (r'배포|Deploy|롤링|블루-그린|카나리|IaC|Terraform|Ansible|컨테이너|가상화',['배포']),
 (r'보안|인증|IAM|TLS|암호화|방화벽|DMZ|시크릿|Secret|최소 권한|공격 표면',['보안']),
]
def extras(title):
    """주제 이름 → 보조 태그 후보(순서대로, 중복 없이). 주 태그 제외·개수 제한은 build_skills 에서."""
    out=[]
    for pat,tgs in SEE:
        if re.search(pat,title):
            out+=[t for t in tgs if t not in out]
    return out
def tag(unit_tag,t,topic_tags=None):
    """우선순위: 과목 설정의 topic_tags(주제 이름 그대로, 그 강의에만) > OV(모든 과목) > 단원 기본 태그."""
    if topic_tags and t in topic_tags: return topic_tags[t]
    for pat,tg in OV:
        if re.search(pat,t): return tg
    return unit_tag
def main():
    data=json.load(open(sys.argv[1]))
    cnt=collections.Counter(); where=collections.defaultdict(set); out=[]
    for x in data:
        out.append(f"\n## {x['title']}\n\n{'https://claude.ai/artifact/'+x['id']}\n")
        for ui,(u,ts) in enumerate(x['units']):
            if u: out.append(f"\n**{u}**\n")
            if not ts: ts=[u]
            for t in ts:
                t=t[0] if isinstance(t,list) else t
                t=re.sub(r'\s*p\.\d[\d–·, ]*$','',re.sub(r' · p\.\d[\d–]*$','',t)).strip()
                g=tag(x['tags'][ui],t); cnt[g]+=1; where[g].add(x['title'][:20])
                out.append(f"- {t} `{g}`")
    open(sys.argv[2],'w').write('\n'.join(out)+'\n')
    for g,c in cnt.most_common(): print(g,c,sorted(where[g]))
    print('total',sum(cnt.values()))

if __name__=='__main__': main()
