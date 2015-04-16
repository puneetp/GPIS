function [tsdf_surface, varargout] = ...
    compute_tsdf_surface_thresholding(tsdf, surf_thresh)

win = 3;
tsdf_dims = size(tsdf);

% compute masks
inside_mask = tsdf < 0;
outside_mask = tsdf > 0;

% get surface points
SE = strel('square', win);
outside_di = imdilate(outside_mask, SE);
tsdf_surface = abs(tsdf) < surf_thresh;

surf_ind = find(tsdf_surface == 1);
inside_ind = find(inside_mask == 1);
outside_ind = find(outside_mask == 1);

if numel(tsdf_dims) == 3
    [surf_x, surf_y, surf_z] = ind2sub(tsdf_dims, surf_ind);
    
    if nargout > 0
        varargout{1} = [surf_x(:) surf_y(:) surf_z(:)];
    end

    [inside_x, inside_y, inside_z] = ind2sub(tsdf_dims, inside_ind);
    if nargout > 1
        varargout{2} = [inside_x(:) inside_y(:) inside_z(:)];
    end

    [outside_x, outside_y, outside_z] = ind2sub(tsdf_dims, inside_ind);
    if nargout > 2
        varargout{3} = [outside_x(:) outside_y(:) outside_z(:)];
    end
else
    [surf_x, surf_y] = ind2sub(tsdf_dims, surf_ind); 
   
    if nargout > 0
        varargout{1} = [surf_y(:) surf_x(:)];
    end

    [inside_x, inside_y] = ind2sub(tsdf_dims, inside_ind);
    if nargout > 1
        varargout{2} = [inside_x(:) inside_y(:)];
    end

    [outside_x, outside_y] = ind2sub(tsdf_dims, outside_ind);
    if nargout > 2
        varargout{3} = [outside_x(:) outside_y(:)];
    end
end

end

