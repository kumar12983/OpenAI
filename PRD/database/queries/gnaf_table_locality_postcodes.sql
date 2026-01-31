 create table locality_postcodes as 
  select distinct ad.legal_parcel_id, ad.address_site_pid, loc.locality_pid, locality_name, ad.postcode, st.state_name, st.state_abbreviation 
  from locality loc
  INNER JOIN address_detail ad on ad.locality_pid = loc.locality_pid
  INNER JOIN state st on st.state_pid = loc.state_pid
  ;