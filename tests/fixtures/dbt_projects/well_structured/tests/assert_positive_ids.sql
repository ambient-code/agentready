select * from {{ ref('stg_customers') }}
where customer_id < 0
