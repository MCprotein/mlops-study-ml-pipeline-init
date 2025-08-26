-- Create database
create database if not exists temp;

-- Drop existing table
drop table if exists temp.ineligible_loan_model_features_01;

-- Create first feature table
create table temp.ineligible_loan_model_features_01 as
select a.applicant_id
    ,a.cust_id
    ,b.gender
    ,b.married
    ,b.education
    ,b.self_employed
    ,a.applicant_income
    ,a.coapplicant_income
    ,a.loan_amount_term
    ,a.credit_history
    ,a.property_area
from mlops.loan_applicant_info a left outer join
    mlops.cust_info           b on (    a.applicant_date = b.base_dt
                                    and a.cust_id = b.cust_id)
where a.applicant_date = '{{ macros.ds_add(ds, -1) | replace("-", "") }}';

-- Drop existing table
drop table if exists temp.ineligible_loan_model_features_02;

-- Create second feature table
create table temp.ineligible_loan_model_features_02 as
select c.cust_id
      ,c.family_dependents
  from (select a.cust_id
              ,case when count(1) >= 3
                    then '3+'
                    else cast(count(1) as char)
                end as family_dependents
          from mlops.loan_applicant_info a inner join
               mlops.family_info         b on (    a.applicant_date = b.base_dt
                                               and a.cust_id = b.cust_id)
         where a.applicant_date between '20230601' and '20231130'
         group by a.cust_id
       ) c;

-- Delete existing data
delete from mlops.ineligible_loan_model_features
where base_dt = '{{ macros.ds_add(ds, -1) | replace("-", "") }}';

-- Insert into final feature table
insert
    into mlops.ineligible_loan_model_features
    (base_dt
    ,applicant_id
    ,gender
    ,married
    ,family_dependents
    ,education
    ,self_employed
    ,applicant_income
    ,coapplicant_income
    ,loan_amount_term
    ,credit_history
    ,property_area
    )
select '{{ macros.ds_add(ds, -1) | replace("-", "") }}' as base_dt
      ,a.applicant_id
      ,a.gender
      ,a.married
      ,b.family_dependents
      ,a.education
      ,a.self_employed
      ,a.applicant_income
      ,a.coapplicant_income
      ,a.loan_amount_term
      ,a.credit_history
      ,a.property_area
  from temp.ineligible_loan_model_features_01 a left outer join
       temp.ineligible_loan_model_features_02 b on (a.cust_id = b.cust_id);