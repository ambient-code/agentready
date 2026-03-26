select
    customer_id,
    customer_name
from {{ ref('stg_customers') }}
