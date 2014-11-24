function [ best_grasp ] = ucb( grasp_samples,num_grasps,shapeParams,experimentConfig,constructionResults  )
%THOMPSON_SAMPLING Summary of this function goes here
%   Detailed explanation goes here

    Total_Iters = 20000; 
    i = 1; 
    ts = true; 
    prune = false; 
    regret = zeros(Total_Iters+1000,1); 

         

    for interval = 1:20
        Storage = {};
        Value = zeros(num_grasps,4); 
        t = 1;
        for i=1:num_grasps
     
            [Q] = evaluate_grasp(i,grasp_samples,shapeParams,experimentConfig);

            UCB_part = 1; 
            Value(i,1) =  Q; 
            Value(i,2) = 1; 
            Value(i,3) = Value(i,1)/t; 
            Value(i,4) = UCB_part; 
            
            [v best_grasp] = max(Value(:,3));
            regret(t) =(interval-1)/interval*regret(t) + (1/interval)*compute_regret_pfc(best_grasp);
            t=t+1; 
        end


        i = 1
        not_sat = true; 
         while(i<Total_Iters && not_sat)
            %i
            if(ts) 
                grasp = get_grasp(Value,t); 
            elseif(prune)
                np_grasp = not_pruned(Value); 
                grasp_idx = randi(length(np_grasp)); 
                grasp = np_grasp(grasp_idx); 
            else
                grasp = randi(num_grasps);  
            end

            [Q, grasp_samples] = evaluate_grasp(grasp,grasp_samples,shapeParams,experimentConfig);
            
            if(Q == -1)
                not_sat = false; 
                break;
            end
            
            UCB_part = sqrt(1/(Value(grasp,2))); 
            Value(grasp,1) =  Value(grasp,1)+Q; 
            Value(grasp,2) = Value(grasp,2)+1; 
            Value(grasp,3) = Value(grasp,1)/Value(grasp,2); 
            Value(grasp,4) = UCB_part; 
            
            [v, best_grasp] = max(Value(:,3)); 
            regret(t) = (interval-1)/interval*regret(t) + (1/interval)*compute_regret_pfc(best_grasp);
            i = i+1; 
            t=t+1; 

         end
    end
    if(prune)
        np_grasp = not_pruned(Value);
        size(np_grasp);
    end
    figure;
    plot(regret)
    title('Simple Regret over Samples'); 
    xlabel('Samples'); 
    ylabel('Simple Regret'); 
    
    visualize_value(Value,grasp_samples,constructionResults); 
    
    if(~ts && ~prune)
        %save('marker_bandit_values_pfc','Value');
        save('regret_marker_pfc_mc_ucb','regret','Value');
    elseif(prune)
        save('regret_marker_pfc_sf_ucb','regret','Value');
    else
        save('regret_marker_pfc_ucb','regret','Value');
    end
end


function [not_pruned_grsp] = not_pruned(Value)
 
 high_low = max(Value(:,4)); 
 not_pruned_grsp = find(high_low < Value(:,5));   

end

function [grasp] = get_grasp(Value,t)    
    sigma = 1; 
    
    Value(:,4) = Value(:,4)*sqrt(6*sigma^2*log(t)); 
   
    [v, grasp] = max(Value(:,3)+Value(:,4));
 
end


function [Q, grasp_samples] = evaluate_grasp(grasp,grasp_samples,shapeParams,experimentConfig)
        
        cm = shapeParams.com;
        ca = atan(experimentConfig.frictionCoef);
        
        c = zeros(3,2);
        grasp_stor = grasp; 
        
       
        iter = grasp_samples{grasp_stor}.current_iter;
        if(iter > 1500)
            Q = -1; 
            return;
        end
        if(size(grasp_samples{grasp_stor}.n1_emps,1) < 1500 || size(grasp_samples{grasp_stor}.n2_emps,1) < 1500)
            Q = 0; 
            return 
        end
        n1 = grasp_samples{grasp_stor}.n1_emps(iter,:);
   
        
        n2 = grasp_samples{grasp_stor}.n2_emps(iter,:);
       
        
        norms(:,1) = n1';
        norms(:,2) = n2'; 
        
        c1 = grasp_samples{grasp_stor}.c1_emps(iter,:);
        c2 = grasp_samples{grasp_stor}.c2_emps(iter,:);
        
        c(1:2,1) = grasp_samples{grasp_stor}.loa_1(c1,:)';
        c(1:2,2) = grasp_samples{grasp_stor}.loa_2(c2,:)'; 
        
        if(abs(c(1,1)- c(1,2))<0.001 && abs(c(2,1)-c(2,2))<0.001)
            Q = 0; 
            return;
        end
        
        for k = 1:2
            if(k ==1)
                forces = forces_on_friction_cone(norms(:,k),ca);
            else
                forces = [forces forces_on_friction_cone(norms(:,k),ca)];
            end
        end
        grasp_samples{grasp_stor}.current_iter = iter +1;
        Q = ferrari_canny( [cm 0]',c,forces );
        
        Q = Q>0;

end



