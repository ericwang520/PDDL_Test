(define (domain tokyo_trip)
  (:requirements :strips :typing :action-costs)
  (:types
    day location time_slot counter
  )
  (:predicates
    (at ?loc - location)
    (available ?loc - location)
    (visited ?loc - location)
    (day_now ?d - day)
    (next_day ?d1 ?d2 - day)
    (time_slot_now ?ts - time_slot)
    (next_slot ?ts1 ?ts2 - time_slot)
    (open ?loc - location ?d - day ?ts - time_slot)
    (visited_on_day ?loc - location ?d - day)
    (day_visit_count ?d - day ?n - counter)   ; 每天訪問的景點數量
    (next_count ?n1 ?n2 - counter)            ; 計數器的遞增關係
    (max_visits_reached ?d - day)             ; 標記某天已達到最大訪問量
  )
  (:functions
    (total-cost - number)
    (travel_time ?from - location ?to - location)
    (play_time ?loc - location)
  )
  (:action move
    :parameters (?from - location ?to - location ?d - day ?ts - time_slot)
    :precondition (and
      (at ?from)
      (available ?to)
      (day_now ?d)
      (time_slot_now ?ts)
      (open ?to ?d ?ts)
    )
    :effect (and
      (not (at ?from))
      (at ?to)
      (increase (total-cost) (travel_time ?from ?to))
    )
  )
  (:action visit
    :parameters (?loc - location ?d - day ?ts - time_slot ?n1 ?n2 - counter)
    :precondition (and
      (at ?loc)
      (available ?loc)
      (day_now ?d)
      (time_slot_now ?ts)
      (open ?loc ?d ?ts)
      (day_visit_count ?d ?n1)       ; 當前訪問數量
      (next_count ?n1 ?n2)           ; n2 是 n1 的下一個數
      (not (max_visits_reached ?d))  ; 尚未達到最大訪問量
    )
    :effect (and
      (visited ?loc)
      (visited_on_day ?loc ?d)
      (not (day_visit_count ?d ?n1))
      (day_visit_count ?d ?n2)
      (when (= ?n2 c2)              ; 如果訪問計數達到 2
        (max_visits_reached ?d))    ; 標記已達最大訪問量
      (increase (total-cost) (play_time ?loc))
    )
  )
  (:action advance_slot
    :parameters (?ts1 - time_slot ?ts2 - time_slot ?d - day)
    :precondition (and
      (time_slot_now ?ts1)
      (day_now ?d)
      (next_slot ?ts1 ?ts2)
    )
    :effect (and
      (not (time_slot_now ?ts1))
      (time_slot_now ?ts2)
      (increase (total-cost) 0)
    )
  )
  (:action advance_day
    :parameters (?d1 - day ?d2 - day)
    :precondition (and
      (day_now ?d1)
      (next_day ?d1 ?d2)
      (time_slot_now ts_23)
    )
    :effect (and
      (not (day_now ?d1))
      (day_now ?d2)
      (not (time_slot_now ts_23))
      (time_slot_now ts_8)
      (increase (total-cost) 0)
    )
  )
)
